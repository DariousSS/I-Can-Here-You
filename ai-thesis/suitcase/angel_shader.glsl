// 左边那个天使（故事用的简单版）：翅膀底图 + 22 只翅膀小眼睛 + 中间大眼睛的瞳孔，全在这一个着色器里画
// 输入 0 = 天使底图 wings_pixel_base.png（1344x1344）
// uA = (形状的宽高比, 时间（秒）, 警报 0~1, 整体亮度 0~1)
//      警报 0 = 白色、所有小眼睛都闭着（只剩一条眼皮线）；警报 1 = 变红、眼睛变大并全部睁开、整体抖一抖
// uB = (视线目标 x, y（形状自己的 0~1 坐标，y 向上；一般是行李箱盖子的位置）, 天使大小倍数, 只睁眼不变红的程度 0~1（白色天使用）)
uniform vec4 uA;
uniform vec4 uB;
out vec4 fragColor;

const float IMG = 1344.0;
const int N = 22;
const vec4 EYES[N] = vec4[N](
    vec4(412.0, 844.0, 60.0, 2.69658),
    vec4(255.0, 752.0, 76.0, 3.06500),
    vec4(165.0, 628.0, 68.0, -2.96209),
    vec4(352.0, 602.0, 60.0, -2.78831),
    vec4(405.0, 414.0, 58.0, -2.28824),
    vec4(300.0, 269.0, 52.0, -2.26050),
    vec4(225.0, 474.0, 60.0, -2.63849),
    vec4(398.0, 952.0, 50.0, 2.43901),
    vec4(110.0, 784.0, 46.0, 3.02820),
    vec4(500.0, 484.0, 42.0, -2.20060),
    vec4(360.0, 159.0, 40.0, -2.07835),
    vec4(932.0, 844.0, 60.0, 0.44502),
    vec4(1089.0, 752.0, 76.0, 0.07659),
    vec4(1179.0, 628.0, 68.0, -0.17951),
    vec4(992.0, 602.0, 60.0, -0.35328),
    vec4(939.0, 414.0, 58.0, -0.85336),
    vec4(1044.0, 269.0, 52.0, -0.88110),
    vec4(1119.0, 474.0, 60.0, -0.50310),
    vec4(946.0, 952.0, 50.0, 0.70258),
    vec4(1234.0, 784.0, 46.0, 0.11339),
    vec4(844.0, 484.0, 42.0, -0.94099),
    vec4(984.0, 159.0, 40.0, -1.06324)
);

float hash(vec2 p)
{
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main()
{
	vec2 uv = vUV.st;
	float asp = max(uA.x, 0.01);
	float T = uA.y;
	float al = clamp(uA.z, 0.0, 1.0);
	float vis = clamp(uA.w, 0.0, 1.0);
	float side = max(uB.z, 0.05) * min(1.0, asp);
	vec2 loc = vec2((uv.x - 0.5) * asp, uv.y - 0.5) / side;
	vec2 ip = (loc + 0.5) * IMG;
	float tk = floor(T * 18.0);
	ip += (vec2(hash(vec2(tk, 1.0)), hash(vec2(tk, 2.0))) - 0.5) * 16.0 * al;
	if (vis <= 0.001 || ip.x < 0.0 || ip.y < 0.0 || ip.x > IMG || ip.y > IMG) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	vec4 col = texture(sTD2DInputs[0], ip / IMG);
	vec2 tloc = vec2((uB.x - 0.5) * asp, uB.y - 0.5) / side;
	vec2 tip = (tloc + 0.5) * IMG;
	vec2 sp = (floor(ip / 6.0) + 0.5) * 6.0;
	float line = 6.0;
	for (int i = 0; i < N; i++) {
		vec4 e = EYES[i];
		float a = e.z * (1.0 + 0.9 * al);
		vec2 d = sp - e.xy;
		if (length(d) > a * 1.3) {
			continue;
		}
		float ca = cos(e.w), sa = sin(e.w);
		vec2 l = vec2(d.x * ca + d.y * sa, -d.x * sa + d.y * ca);
		float b = a * 0.5;
		float t = mod(T + float(i) * 1.7, 5.5);
		float bl = 1.0 - ((t < 0.3) ? max(0.0, 1.0 - abs(t - 0.1) / 0.12) : 0.0);
		float ti = 0.12 + 0.70 * fract(float(i) * 0.618);
		float op = smoothstep(ti, ti + 0.16, max(al, clamp(uB.w, 0.0, 1.0)));
		float h = b * max(0.10, bl) * op;
		float sx = clamp(l.x / a, -1.0, 1.0);
		float hh = h * (1.0 - sx * sx);
		if (op < 0.02) {
			float lid = -b * 0.40 * (1.0 - sx * sx);
			if (abs(l.x) < a && abs(l.y - lid) < line * 0.5) {
				col = vec4(1.0);
			}
			continue;
		}
		bool inside = (abs(l.x) < a) && (abs(l.y) < hh);
		bool edge = (abs(l.x) < a) && (abs(abs(l.y) - hh) < line * 0.5);
		if (!inside && !edge) {
			continue;
		}
		vec2 g = tip - (e.xy);
		float gl = length(g) + 0.0001;
		vec2 n = g / gl;
		float k = min(1.0, gl / 500.0);
		vec2 ln = vec2(n.x * ca + n.y * sa, -n.x * sa + n.y * ca);
		vec2 pc = vec2(ln.x * k * a * 0.38, ln.y * k * b * 0.40);
		float rr = b * 0.60;
		float dd = length(l - pc);
		bool ring = inside && abs(dd - rr) < line * 0.5;
		bool pup = inside && dd < max(rr * 0.42, 7.0);
		if (ring || pup || edge) {
			col = vec4(1.0);
		} else {
			col = vec4(0.0, 0.0, 0.0, 1.0);
		}
	}
	vec2 cc = vec2(672.0, 720.0);
	vec2 gc = tip - cc;
	float gcl = length(gc) + 0.0001;
	vec2 pcen = cc + gc / gcl * min(1.0, gcl / 400.0) * 55.0;
	float pr = 36.0 * (1.0 + 0.6 * al);
	if (length(sp - pcen) < pr) {
		col = vec4(1.0);
	}
	vec3 tint = vec3(1.0, 1.0 - 0.72 * al, 1.0 - 0.72 * al);
	float aa = col.a * vis;
	fragColor = TDOutputSwizzle(vec4(col.rgb * tint * aa, aa));
}
