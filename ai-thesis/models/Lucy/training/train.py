#!/usr/bin/env python3
"""
Pretrain a small unconditional DDPM diffusion model at 128x128 from scratch
on a single GPU (RTX 3060-friendly: fp16 AMP, ~50M-param UNet).

Default dataset: tglcourse/CelebA-faces-cropped-128 (~202k SFW 128x128 face crops).
Alternative:     huggan/flowers-102-categories

Training stops at min(--max_train_steps, --max_hours wall clock), so it is
safe to leave running overnight.

Usage:
    python train.py --output_dir runs/celeba128

Sample from the finished run:
    from diffusers import DiffusionPipeline
    pipe = DiffusionPipeline.from_pretrained("runs/celeba128/final").to("cuda")
    pipe(batch_size=8).images[0].save("sample.png")
"""

import argparse
import copy
import math
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.utils import make_grid, save_image

from datasets import load_dataset
from diffusers import DDIMScheduler, DDPMPipeline, DDPMScheduler, UNet2DModel


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset_name", default="tglcourse/CelebA-faces-cropped-128")
    p.add_argument("--split", default="train")
    p.add_argument("--image_column", default="image")
    p.add_argument("--resolution", type=int, default=128)
    p.add_argument("--output_dir", default="runs/celeba128")
    p.add_argument("--train_batch_size", type=int, default=16)
    p.add_argument("--gradient_accumulation_steps", type=int, default=1)
    p.add_argument("--max_train_steps", type=int, default=60_000)
    p.add_argument("--max_hours", type=float, default=13.5,
                   help="hard wall-clock budget; stops at steps OR hours, whichever first")
    p.add_argument("--learning_rate", type=float, default=1e-4)
    p.add_argument("--warmup_steps", type=int, default=500)
    p.add_argument("--ema_decay", type=float, default=0.9999)
    p.add_argument("--num_train_timesteps", type=int, default=1000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dataloader_num_workers", type=int, default=4)
    p.add_argument("--log_every", type=int, default=100)
    p.add_argument("--sample_every", type=int, default=3000)
    p.add_argument("--num_sample_images", type=int, default=16)
    p.add_argument("--ckpt_every", type=int, default=20_000)
    p.add_argument("--keep_ckpts", type=int, default=2)
    p.add_argument("--resume_from", default=None)
    p.add_argument("--channels", type=int, nargs="+", default=[128, 128, 256, 256, 512])
    p.add_argument("--layers_per_block", type=int, default=2)
    p.add_argument("--no_tensorboard", action="store_true")
    return p.parse_args()


def build_unet(resolution, channels, layers_per_block):
    n = len(channels)
    attn_idx = n - 2
    down = ["DownBlock2D"] * n
    up = ["UpBlock2D"] * n
    down[attn_idx] = "AttnDownBlock2D"
    up[n - 1 - attn_idx] = "AttnUpBlock2D"
    return UNet2DModel(
        sample_size=resolution,
        in_channels=3,
        out_channels=3,
        layers_per_block=layers_per_block,
        block_out_channels=tuple(channels),
        down_block_types=tuple(down),
        up_block_types=tuple(up),
    )


def build_dataset(args):
    ds = load_dataset(args.dataset_name, split=args.split)
    tf = transforms.Compose([
        transforms.Resize(args.resolution, interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.CenterCrop(args.resolution),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.5] * 3, [0.5] * 3),
    ])

    def apply(examples):
        return {"images": [tf(img.convert("RGB")) for img in examples[args.image_column]]}

    ds.set_transform(apply)
    return ds


@torch.no_grad()
def ema_update(ema_model, model, decay):
    for pe, pm in zip(ema_model.parameters(), model.parameters()):
        pe.lerp_(pm.data, 1.0 - decay)


@torch.no_grad()
def generate_samples(ema_model, args, device, global_step):
    ema_model.eval()
    ddim = DDIMScheduler(num_train_timesteps=args.num_train_timesteps, beta_schedule="linear")
    ddim.set_timesteps(50)
    g = torch.Generator(device=device).manual_seed(args.seed)
    x = torch.randn(args.num_sample_images, 3, args.resolution, args.resolution,
                    generator=g, device=device, dtype=torch.float16)
    for t in ddim.timesteps:
        tt = t.expand(x.shape[0]).to(device)
        with torch.autocast("cuda", dtype=torch.float16):
            pred = ema_model(x, tt).sample
        x = ddim.step(pred, t, x).prev_sample
    x = (x.float().clamp(-1, 1) + 1.0) / 2.0
    out = Path(args.output_dir) / "samples"
    out.mkdir(parents=True, exist_ok=True)
    save_image(make_grid(x, nrow=int(math.sqrt(x.shape[0]))), out / f"step_{global_step:07d}.png")
    ema_model.train()


def save_checkpoint(path, step, model, ema_model, optimizer, scaler):
    torch.save({
        "step": step,
        "model": model.state_dict(),
        "ema": ema_model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
    }, path)


def prune_checkpoints(ckpt_dir, keep):
    ckpts = sorted(ckpt_dir.glob("step_*.pt"))
    for old in ckpts[:-keep]:
        old.unlink()


def main():
    args = parse_args()
    out = Path(args.output_dir)
    ckpt_dir = out / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    torch.manual_seed(args.seed)
    device = "cuda"
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True

    writer = None
    if not args.no_tensorboard:
        try:
            from torch.utils.tensorboard import SummaryWriter
            writer = SummaryWriter(out / "tb")
        except ImportError:
            pass

    ds = build_dataset(args)
    loader = DataLoader(ds, batch_size=args.train_batch_size, shuffle=True,
                        num_workers=args.dataloader_num_workers, pin_memory=True,
                        drop_last=True)

    model = build_unet(args.resolution, args.channels, args.layers_per_block).to(device)
    ema_model = copy.deepcopy(model).eval()
    for p in ema_model.parameters():
        p.requires_grad_(False)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"model params: {n_params / 1e6:.1f}M | dataset rows: {len(ds)} | "
          f"batch {args.train_batch_size} x accum {args.gradient_accumulation_steps}", flush=True)

    T = args.num_train_timesteps
    noise_sched = DDPMScheduler(num_train_timesteps=T, beta_schedule="linear",
                                prediction_type="epsilon")
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    scaler = torch.amp.GradScaler("cuda")

    start_step = 0
    if args.resume_from:
        st = torch.load(args.resume_from, map_location=device)
        model.load_state_dict(st["model"])
        ema_model.load_state_dict(st["ema"])
        optimizer.load_state_dict(st["optimizer"])
        scaler.load_state_dict(st["scaler"])
        start_step = st["step"]
        print(f"resumed from {args.resume_from} at step {start_step}", flush=True)

    lr_sched = torch.optim.lr_scheduler.LambdaLR(
        optimizer, lambda s: min(1.0, (s + 1) / max(1, args.warmup_steps)),
        last_epoch=start_step - 1)

    accum = args.gradient_accumulation_steps
    model.train()
    optimizer.zero_grad(set_to_none=True)
    data_iter = iter(loader)
    epoch = 0
    t0 = time.time()
    budget_s = args.max_hours * 3600
    running = 0.0

    for step in range(start_step, args.max_train_steps):
        if time.time() - t0 >= budget_s:
            print(f"wall-clock budget of {args.max_hours}h reached at step {step}", flush=True)
            break
        try:
            batch = next(data_iter)
        except StopIteration:
            epoch += 1
            data_iter = iter(loader)
            batch = next(data_iter)

        x0 = batch["images"].to(device, non_blocking=True)
        noise = torch.randn_like(x0)
        timesteps = torch.randint(0, T, (x0.shape[0],), device=device, dtype=torch.long)
        noisy = noise_sched.add_noise(x0, noise, timesteps)

        with torch.autocast("cuda", dtype=torch.float16):
            pred = model(noisy, timesteps).sample
            loss = F.mse_loss(pred.float(), noise)
        scaler.scale(loss / accum).backward()

        if (step + 1) % accum == 0:
            scaler.unscale_(optimizer)
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            lr_sched.step()
            ema_update(ema_model, model, args.ema_decay)
        running += loss.item()

        if writer and (step + 1) % args.log_every == 0:
            writer.add_scalar("train/loss", running / args.log_every, step + 1)
            writer.add_scalar("train/lr", lr_sched.get_last_lr()[0], step + 1)

        if (step + 1) % args.log_every == 0:
            el = time.time() - t0
            sps = (step + 1 - start_step) / max(el, 1e-6)
            eta = min((args.max_train_steps - (step + 1)) / max(sps, 1e-6), budget_s - el)
            print(f"step {step + 1}/{args.max_train_steps} | epoch {epoch} | "
                  f"loss {running / args.log_every:.4f} | grad {grad_norm:.2f} | "
                  f"{sps:.2f} it/s | ETA {max(eta, 0) / 3600:.2f}h", flush=True)
            running = 0.0

        if (step + 1) % args.sample_every == 0:
            generate_samples(ema_model, args, device, step + 1)

        if (step + 1) % args.ckpt_every == 0:
            save_checkpoint(ckpt_dir / f"step_{step + 1}.pt", step + 1,
                            model, ema_model, optimizer, scaler)
            prune_checkpoints(ckpt_dir, args.keep_ckpts)

    save_checkpoint(ckpt_dir / "last.pt", step + 1, model, ema_model, optimizer, scaler)
    generate_samples(ema_model, args, device, step + 1)
    pipe = DDPMPipeline(unet=ema_model,
                        scheduler=DDPMScheduler(num_train_timesteps=T, beta_schedule="linear"))
    pipe.save_pretrained(out / "final")
    if writer:
        writer.close()
    print(f"done: {(time.time() - t0) / 3600:.2f}h | final pipeline at {out / 'final'}", flush=True)


if __name__ == "__main__":
    main()
