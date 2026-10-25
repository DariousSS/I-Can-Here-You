// 蜡笔质感的马赛克模糊（TouchDesigner GLSL TOP 的像素着色器）
// 把画面切成大小不一、边缘歪歪扭扭的色块，每块的位置轻轻抖动、颜色压成几档（像蜡笔涂的），再叠上纸面颗粒和斜着的笔触纹。
// uM = (强度 0~1（0 = 原样通过）, 色块大小（按 512 像素宽的画面算）, 时间（秒）, 0)
uniform vec4 uM;

out vec4 fragColor;

float hash(vec2 p)
{
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p)
{
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}

void main()
{
	vec2 uv = vUV.st;
	vec4 orig = texture(sTD2DInputs[0], uv);
	float amt = uM.x;
	if (amt <= 0.001) {
		fragColor = TDOutputSwizzle(orig);
		return;
	}
	vec2 res = uTD2DInfos[0].res.zw;
	float sc = res.x / 512.0;
	float B = max(uM.y * sc, 2.0);
	vec2 p = uv * res;
	vec2 wob = (vec2(vnoise(p * 0.035 / sc + uM.z * 0.15), vnoise(p * 0.035 / sc + 17.3 - uM.z * 0.1)) - 0.5) * B * 0.9;
	vec2 q = p + wob;
	vec2 cell = floor(q / B);
	vec2 jit = (vec2(hash(cell), hash(cell + 7.7)) - 0.5) * 0.45 * B;
	vec2 c0 = (cell + 0.5) * B + jit - wob * 0.5;
	vec3 acc = vec3(0.0);
	for (int i = 0; i < 4; i++) {
		vec2 o = vec2((i == 0 || i == 3) ? -1.0 : 1.0, (i < 2) ? -1.0 : 1.0) * B * 0.28;
		acc += texture(sTD2DInputs[0], (c0 + o) / res).rgb;
	}
	vec3 col = acc * 0.25;
	float lum = dot(col, vec3(0.299, 0.587, 0.114));
	col = mix(vec3(lum), col, 1.45);
	col = floor(col * 9.0 + 0.5) / 9.0;
	float grain = vnoise(p * 0.9 / sc) * 0.6 + vnoise(p * 2.7 / sc) * 0.4;
	col *= 0.86 + 0.26 * grain;
	float hatch = sin(dot(p / sc, vec2(0.74, 0.67)) * 0.85 + hash(cell) * 6.2831) * 0.5 + 0.5;
	col *= 0.90 + 0.20 * hatch;
	vec2 f = fract(q / B);
	float edge = min(min(f.x, 1.0 - f.x), min(f.y, 1.0 - f.y));
	col *= 0.88 + 0.12 * smoothstep(0.0, 0.14, edge);
	fragColor = TDOutputSwizzle(vec4(mix(orig.rgb, col, amt), orig.a));
}
