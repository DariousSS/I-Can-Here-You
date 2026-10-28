// 蜡笔质感的马赛克模糊（TouchDesigner GLSL TOP 的像素着色器）
// 把画面切成大小不一、边缘歪歪扭扭的色块，每块的位置轻轻抖动、颜色压成几档（像蜡笔涂的），再叠上纸面颗粒和斜着的笔触纹。
// uM = (强度 0~1（0 = 原样通过）, 色块大小 / 涂抹长度（按 512 像素宽的画面算）, 时间（秒）, 风格：0 = 旧的彩色蜡笔色块 / 2 = 油画（顺着方向的长笔触 + Kuwahara 色块）/ 1 = 干笔涂抹（油画棒、水粉：顺着往下拖、竖向刷痕、很暗的橄榄绿和暗紫红、纸面颗粒）)
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
	if (uM.w > 0.5) {
		vec2 p = vec2(uv.x, 1.0 - uv.y) * res;
		float th = 1.5707963 + (vnoise(p * 0.004 / sc) - 0.5) * 0.7;
		vec2 dir = vec2(cos(th), sin(th));
		vec2 perp = vec2(-dir.y, dir.x);
		float bj = (hash(vec2(floor(p.x / (1.6 * sc)), 3.0)) - 0.5) * 5.0 * sc;
		float Ls = uM.y * 1.25 * sc;
		vec3 acc = vec3(0.0);
		for (int i = 0; i < 14; i++) {
			float t = mix(-0.25, 0.75, float(i) / 13.0);
			vec2 q = p + dir * t * Ls + perp * bj;
			acc += texture(sTD2DInputs[0], vec2(q.x / res.x, 1.0 - q.y / res.y)).rgb;
		}
		vec3 c = acc / 14.0;
		float streak = vnoise(vec2(p.x * 0.42 / sc, p.y * 0.012 / sc)) * 0.7 + vnoise(vec2(p.x * 1.1 / sc, p.y * 0.03 / sc)) * 0.3;
		c *= 0.80 + 0.40 * streak;
		float th2 = th + 0.45;
		vec2 d2 = vec2(cos(th2), sin(th2));
		vec3 acc2 = vec3(0.0);
		for (int i = 0; i < 9; i++) {
			float t = mix(-0.2, 0.6, float(i) / 8.0);
			vec2 q = p + d2 * t * Ls * 0.8;
			acc2 += texture(sTD2DInputs[0], vec2(q.x / res.x, 1.0 - q.y / res.y)).rgb;
		}
		c = c * 0.65 + (acc2 / 9.0) * 0.35 * (0.8 + 0.4 * streak);
		float blob = vnoise(p * 0.006 / sc) * 0.6 + vnoise(p * 0.02 / sc) * 0.4;
		c *= 0.55 + 0.9 * blob;
		float lum = (c.r + c.g + c.b) / 3.0;
		c = vec3(lum) + (c - vec3(lum)) * 0.42;
		vec3 shadow = vec3(0.02, 0.03, 0.02);
		vec3 light = vec3(0.80, 0.79, 0.64);
		c = shadow + (light - shadow) * pow(clamp(c * 1.1, 0.0, 1.0), vec3(1.7));
		float mid = clamp(1.0 - abs(lum - 0.40) * 3.2, 0.0, 1.0);
		c += mid * vec3(0.10, -0.03, 0.03);
		c += mid * (blob - 0.5) * vec3(-0.04, 0.07, -0.04);
		c += (hash(p * 1.3) - 0.5) * 0.10;
		vec2 vq = uv - 0.5;
		c *= 1.0 - 0.35 * dot(vq, vq) * 2.2;
		fragColor = TDOutputSwizzle(vec4(mix(orig.rgb, clamp(c, 0.0, 1.0), amt), orig.a));
		return;
	}
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
