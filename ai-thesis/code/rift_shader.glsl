// 裂缝里的一堆眼睛（TouchDesigner GLSL TOP 的像素着色器，像素风：按 6x6 的格子画）
// 画面左右边缘各有一道竖着的裂缝（锯齿边），缝里排着 7 只眼睛，一起盯着对应的面具；偏差高时裂开、变红
// uA = (左缝张开程度 0~1, 右缝张开程度 0~1, 时间（秒）, 总开关 0~1)
// uB = (左缝视线目标 x, y, 右缝视线目标 x, y)（画布像素，y 向上）
// uC = (左缝变红程度 0~1, 右缝变红程度 0~1, 左缝中心高度 y, 右缝中心高度 y)（画布像素，y 向上）
uniform vec4 uA;
uniform vec4 uB;
uniform vec4 uC;

out vec4 fragColor;

const vec2 RES = vec2(1920.0, 1080.0);
const float BLK = 6.0;
const float SH = 330.0;
const float WH = 112.0;
const float XEDGE = 150.0;
const int NE = 7;
const vec3 E[NE] = vec3[NE](
    vec3(-26.0, -270.0, 46.0), vec3(24.0, -180.0, 60.0), vec3(-28.0, -90.0, 70.0), vec3(22.0, 0.0, 76.0),
    vec3(-26.0, 90.0, 70.0), vec3(24.0, 180.0, 60.0), vec3(-22.0, 270.0, 46.0)
);

float hs(float n)
{
	return fract(sin(n * 12.9898) * 43758.5453);
}

vec4 slit(vec2 p, vec2 c, float o, vec2 T, float red, float tm)
{
	if (o <= 0.01) {
		return vec4(0.0);
	}
	vec2 d = p - c;
	float oh = smoothstep(0.0, 0.5, o);
	float ow = smoothstep(0.2, 1.0, o);
	float halfH = SH * oh;
	float halfW = WH * ow;
	if (halfH < 4.0 || abs(d.y) > halfH + BLK) {
		return vec4(0.0);
	}
	float t = clamp(abs(d.y) / halfH, 0.0, 1.0);
	float hw = halfW * (1.0 - pow(t, 1.5));
	hw += (hs(floor(d.y / BLK) + 7.0) - 0.5) * 0.30 * halfW * (1.0 - t);
	hw = max(hw, 0.0);
	vec3 lc = mix(vec3(1.0), vec3(1.0, 0.28, 0.28), red);
	vec4 col = vec4(0.0);
	float ax = abs(d.x);
	bool inside = (ax < hw) && (abs(d.y) <= halfH);
	bool edge = (abs(ax - hw) < BLK * 0.75) && (abs(d.y) <= halfH + BLK * 0.5) && (hw > 1.0);
	if (inside) {
		col = vec4(0.0, 0.0, 0.0, 1.0);
	}
	if (edge) {
		col = vec4(lc, 1.0);
	}
	float eo = smoothstep(0.45, 0.9, o);
	if (eo > 0.01) {
		for (int i = 0; i < NE; i++) {
			vec3 e = E[i];
			vec2 ec = vec2(e.x * ow, e.y * oh);
			float a = e.z * eo;
			vec2 l = d - ec;
			if (abs(l.x) > a || abs(l.y) > a * 0.6) {
				continue;
			}
			float b = a * 0.5;
			float tt = mod(tm + float(i) * 1.3, 5.0);
			float bl = 1.0 - ((tt < 0.3) ? max(0.0, 1.0 - abs(tt - 0.1) / 0.12) : 0.0);
			float h = b * max(0.10, bl);
			float sx = clamp(l.x / a, -1.0, 1.0);
			float hh = h * (1.0 - sx * sx);
			bool in2 = (abs(l.x) < a) && (abs(l.y) < hh);
			bool ed = (abs(l.x) < a) && (abs(abs(l.y) - hh) < BLK * 0.5);
			if (!in2 && !ed) {
				continue;
			}
			vec2 g = T - (c + ec);
			float gl = length(g) + 0.0001;
			vec2 n = g / gl;
			float k = min(1.0, gl / 500.0);
			vec2 pc = vec2(n.x * k * a * 0.38, n.y * k * b * 0.40);
			float rr = b * 0.6;
			float dd = length(l - pc);
			bool ring = in2 && abs(dd - rr) < BLK * 0.5;
			bool pup = in2 && dd < max(rr * 0.42, BLK * 1.2);
			col = (ring || pup || ed) ? vec4(lc, 1.0) : vec4(0.0, 0.0, 0.0, 1.0);
		}
	}
	return col;
}

void main()
{
	if (uA.w <= 0.001) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	vec2 frag = vUV.st * RES;
	vec2 p = (floor(frag / BLK) + 0.5) * BLK;
	vec4 cL = slit(p, vec2(XEDGE, uC.z), uA.x, uB.xy, uC.x, uA.z);
	vec4 cR = slit(p, vec2(RES.x - XEDGE, uC.w), uA.y, uB.zw, uC.y, uA.z);
	vec4 col = cL;
	if (cR.a > 0.5) {
		col = cR;
	}
	fragColor = TDOutputSwizzle(col);
}
