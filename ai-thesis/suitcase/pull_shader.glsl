// 入侵时，两张脸之间的"拉扯"：像电视机故障，右边那张脸的像素被一行行横着拉过去，连到左边的面具
// 输入 0 = 右边的脸（mask_R）；输出是整张画布大小（1920x1080），在 Kantan 里给一个盖满画布的形状用
// uP = (右脸中心 x, y, 左面具中心 x, y)，都是 0~1 的画布坐标（y 向上）
// uQ = (右脸半高, 左面具半高, 强度 0~1, 时间（秒）)
uniform vec4 uP;
uniform vec4 uQ;
out vec4 fragColor;

float hash(vec2 p)
{
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main()
{
	vec2 uv = vUV.st;
	vec2 src = uP.xy;
	vec2 dst = uP.zw;
	float amt = uQ.z;
	float T = uQ.w;
	float t = (uv.x - dst.x) / (src.x - dst.x);
	if (t < 0.0 || t > 1.0 || amt < 0.01) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	float yc = mix(dst.y, src.y, t);
	float hh = mix(uQ.y, uQ.x, t) * 1.05;
	float dy = uv.y - yc;
	if (abs(dy) > hh) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	float row = floor(uv.y * 90.0);
	float tick = floor(T * 12.0);
	float r1 = hash(vec2(row, tick));
	float r2 = hash(vec2(row, 3.0 + floor(T * 4.0)));
	float u = clamp(0.5 + (r1 - 0.5) * 0.35 + (r2 - 0.5) * 0.2, 0.05, 0.95);
	float v = 0.5 + dy / (2.0 * hh);
	vec2 q = vec2(u, v);
	float sp = 0.03 * amt;
	vec3 col;
	col.r = texture(sTD2DInputs[0], q + vec2(sp, 0.0)).r;
	col.g = texture(sTD2DInputs[0], q).g;
	col.b = texture(sTD2DInputs[0], q - vec2(sp, 0.0)).b;
	float scan = step(0.965, hash(vec2(row, tick + 11.0)));
	col += vec3(0.55, 1.0, 0.9) * scan * 0.7;
	float ends = smoothstep(0.0, 0.18, t) * smoothstep(0.0, 0.12, 1.0 - t);
	float flick = 0.55 + 0.45 * step(0.35, hash(vec2(row * 0.37, floor(T * 20.0))));
	float a = amt * ends * flick;
	fragColor = TDOutputSwizzle(vec4(col * a, a));
}
