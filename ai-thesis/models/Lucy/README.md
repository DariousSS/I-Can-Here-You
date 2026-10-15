---
license: apache-2.0
library_name: diffusers
pipeline_tag: unconditional-image-generation
tags:
  - diffusers
  - ddpm
  - unconditional-image-generation
  - diffusion
  - faces
  - pytorch
  - safetensors
datasets:
  - tglcourse/CelebA-faces-cropped-128
---

# Lucy

**Lucy** is a small unconditional denoising diffusion model (DDPM) that generates
128×128 RGB face images. It was trained from scratch — no pretrained
initialization, no fine-tuning of an existing checkpoint — on a single consumer
GPU (RTX 3060, 12 GB) in under ten hours.

Weights are open: Apache-2.0, `safetensors`, plus the complete training script
and the raw training log used to produce them. Everything needed to reproduce
the run is in this repo.

![Samples from Lucy](samples/sample_grid.png)

---

## Quick start

```bash
pip install diffusers transformers accelerate torch safetensors
```

```python
from diffusers import DDPMPipeline

pipe = DDPMPipeline.from_pretrained("opencerebral/Lucy").to("cuda")
images = pipe(batch_size=4).images
images[0].save("face.png")
```

### Faster sampling with DDIM

The default DDPM scheduler runs the full 1000-step reverse chain. The samples in
this card were generated with **DDIM at 50 steps**, which is ~20× faster and what
the training script itself uses for its periodic previews:

```python
import torch
from diffusers import DDIMPipeline, DDIMScheduler, UNet2DModel

unet = UNet2DModel.from_pretrained("opencerebral/Lucy", subfolder="unet").to("cuda")
sched = DDIMScheduler(num_train_timesteps=1000, beta_schedule="linear")
pipe = DDIMPipeline(unet=unet, scheduler=sched).to("cuda")

images = pipe(batch_size=16, num_inference_steps=50,
              generator=torch.manual_seed(42)).images
```

The model is unconditional: there is no text prompt, no class label, and no
guidance. The only control you have over the output is the initial noise, i.e.
the random seed.

---

## Model details

| | |
|---|---|
| Architecture | `UNet2DModel` (diffusers), epsilon-prediction |
| Parameters | **71.4 M** |
| Resolution | 128 × 128, RGB |
| Conditioning | none (unconditional) |
| Block channels | `[128, 128, 256, 256, 512]` |
| Down blocks | `DownBlock2D ×3`, `AttnDownBlock2D`, `DownBlock2D` |
| Up blocks | `UpBlock2D`, `AttnUpBlock2D`, `UpBlock2D ×3` |
| Layers per block | 2 |
| Attention head dim | 8 (self-attention at the 16×16 stage and in the mid block) |
| Norm | GroupNorm, 32 groups, eps 1e-5 |
| Activation | SiLU |
| Timestep embedding | positional |
| Weights format | `safetensors`, fp32 (286 MB) |
| diffusers version | 0.39.0 |

### Noise schedule

Linear beta schedule, `beta_start = 1e-4`, `beta_end = 0.02`, `T = 1000`
timesteps, `prediction_type = "epsilon"`, `variance_type = "fixed_small"`,
`clip_sample = True`. Standard DDPM (Ho et al., 2020) settings.

Attention sits at exactly one resolution (the second-to-last downsampling
stage, 16×16). That is deliberate: at 128×128 a full-resolution attention map is
what blows up memory on a 12 GB card, and a single mid-depth attention stage
recovers most of the global coherence — face symmetry, consistent lighting
across the image — for very little cost.

---

## Training

| | |
|---|---|
| Dataset | [`tglcourse/CelebA-faces-cropped-128`](https://huggingface.co/datasets/tglcourse/CelebA-faces-cropped-128) — 192,469 rows used |
| Hardware | 1 × NVIDIA GeForce RTX 3060 (12 GB) |
| Precision | fp16 AMP (`torch.autocast`) with `GradScaler`; TF32 matmul enabled |
| Optimizer | AdamW, lr `1e-4`, 500-step linear warmup, constant thereafter |
| Batch size | 16 (no gradient accumulation) |
| Grad clipping | global norm 1.0 |
| EMA | decay 0.9999, updated every optimizer step; **the released weights are the EMA weights** |
| Steps | 60,000 (≈ 5 epochs) |
| Wall clock | **9.54 hours**, ~1.75 it/s steady state |
| Seed | 42 |
| Loss | MSE on predicted noise, computed in fp32 |

Augmentation was resize → center crop to 128 → random horizontal flip →
normalize to `[-1, 1]`. Nothing else.

### Loss curve

Training loss over the run, read from `training/train.log`:

| step | loss |
|---:|---:|
| 100 | 0.5997 |
| 200 | 0.0715 |
| 300 | 0.0467 |
| 60,000 | 0.0131 |

Note that the *first* logged value is the only large one — DDPM epsilon-loss
collapses almost immediately to the ~0.05 range because most sampled timesteps
are easy, and the remaining 59,700 steps buy a slow grind from 0.047 down to
0.013. Loss is a poor progress signal here; the sample grids are the real one.

### Training progression

`training/progress/` contains an EMA sample grid rendered every 3,000 steps
(`step_0003000.png` … `step_0060000.png`), all from the same fixed seed, so you
can watch the same 16 latents resolve from noise into faces over the run.

---

## What's in this repo

```
model_index.json                 DDPMPipeline definition
unet/                            UNet2DModel config + EMA weights (safetensors)
scheduler/                       DDPMScheduler config
samples/sample_grid.png          16 samples, DDIM 50 steps, seed 42
samples/one_face.png             single 128x128 sample
training/train.py                the full training script
training/run.sh                  the exact launch command for this run
training/train.log               complete stdout of the 60k-step run
training/progress/               EMA previews every 3,000 steps
```

### Reproducing

```bash
pip install torch torchvision diffusers datasets accelerate tensorboard
bash training/run.sh          # edit --output_dir first
```

The script stops at `min(--max_train_steps, --max_hours)`, checkpoints every
20,000 steps keeping the last 2, and writes a ready-to-load `DDPMPipeline` to
`<output_dir>/final` when it finishes. It supports `--resume_from` for restarts.

Optimizer-state checkpoints (`step_*.pt`, ~1.2 GB each) are **not** included
here — they are large and only useful for resuming this specific run. The EMA
weights in `unet/` are the artifact worth keeping.

---

## Limitations

Be realistic about what a 71M-parameter model trained for 9.5 hours produces:

- **Fidelity.** Outputs are recognizably faces with plausible structure,
  lighting, and hair, but they are soft, and fine detail — teeth, eyes at close
  range, jewelry, text — is often wrong. Compare the samples above before
  assuming this is drop-in usable.
- **Backgrounds are mush.** CelebA is celebrity photos with wildly varied,
  cluttered backgrounds. The model has learned "a colorful blur behind a face"
  and little more.
- **Occasional structural failures.** A minority of samples have distorted or
  doubled features. There is no rejection sampling or guidance to filter these.
- **No control.** Unconditional means unconditional. You cannot ask for an age,
  an expression, a pose, or a style. Seed search is the only lever.
- **Dataset bias.** CelebA is a celebrity face dataset and is well documented as
  skewed in age, skin tone, and attractiveness-as-labeled. Lucy reproduces that
  skew faithfully. It is not a representative sample of human faces and should
  not be treated as one.
- **Resolution.** Fixed at 128×128. The UNet's `sample_size` is 128 and it will
  degrade badly if you ask it for other sizes.

## Intended use

Research, education, and demonstration of small-scale from-scratch diffusion
training. It is a good teaching artifact: the whole pipeline is one 270-line
script, and the log shows exactly what a 60k-step run costs on hardware people
actually own.

**Not** intended for generating imagery of, or presented as, real people. The
model was trained on photographs of real individuals; while its outputs are not
reconstructions of specific training images, do not use it to imply the depiction
of any real person, and do not use it in any identity, verification, or
surveillance context.

## Licensing

- **Model weights and code in this repo: Apache-2.0.**
- **Training data is a separate matter.** The weights derive from CelebA, which
  is released for **non-commercial research use only** under its original terms.
  The Apache-2.0 grant here covers what the repo authors can grant; it does not
  and cannot override upstream dataset terms. If you plan to use Lucy
  commercially, review the CelebA license yourself first — the honest reading is
  that a CelebA-derived model inherits that non-commercial restriction.

## Citation

DDPM, the method this implements:

```bibtex
@inproceedings{ho2020ddpm,
  title  = {Denoising Diffusion Probabilistic Models},
  author = {Ho, Jonathan and Jain, Ajay and Abbeel, Pieter},
  booktitle = {Advances in Neural Information Processing Systems},
  year   = {2020}
}
```

This model:

```bibtex
@misc{lucy2026,
  title  = {Lucy: a 71M-parameter unconditional face diffusion model trained from scratch},
  author = {OpenCerebral},
  year   = {2026},
  howpublished = {\url{https://huggingface.co/opencerebral/Lucy}}
}
```
