// 翅膀上的小眼睛（像素风：按翅膀图的 6x6 像素格对齐，线条正好一格宽；TouchDesigner GLSL TOP 的像素着色器；由 make_angel_eyes.py 从这个模板生成 angel_eyes_shader.glsl，别直接改生成的那个）
// uA = (翅膀图中心的画布位置 x, y（像素，y 向上）, 翅膀画在画布上的宽, 高)
// uB = (视线目标的画布位置 x, y（像素，y 向上）, 时间（秒）, 开关 0~1)
// uC = (睁眼程度 0~1：0 = 所有小眼睛都闭着（只剩一条线），越大越多的眼睛睁开；每只眼睛睁开的时机不同, 0, 0, 0)
uniform vec4 uA;
uniform vec4 uB;
uniform vec4 uC;

out vec4 fragColor;

const float IMG = 1344.0;
const vec2 RES = vec2(1920.0, 1080.0);
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

void main()
{
	vec2 frag = vUV.st * RES;
	vec2 ip = ((frag - uA.xy) / uA.zw + 0.5) * IMG;
	if (uB.w <= 0.001 || ip.x < -50.0 || ip.y < -50.0 || ip.x > IMG + 50.0 || ip.y > IMG + 50.0) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	ip = (floor(ip / 6.0) + 0.5) * 6.0;
	float line = 6.0;
	vec4 col = vec4(0.0);
	for (int i = 0; i < N; i++) {
		vec4 e = EYES[i];
		float a = e.z;
		vec2 d = ip - e.xy;
		if (length(d) > a * 1.3) {
			continue;
		}
		float ca = cos(e.w), sa = sin(e.w);
		vec2 l = vec2(d.x * ca + d.y * sa, -d.x * sa + d.y * ca);
		float b = a * 0.5;
		float t = mod(uB.z + float(i) * 1.7, 5.5);
		float bl = 1.0 - ((t < 0.3) ? max(0.0, 1.0 - abs(t - 0.1) / 0.12) : 0.0);
		float ti = 0.12 + 0.70 * fract(float(i) * 0.618);
		float op = smoothstep(ti, ti + 0.16, uC.x);
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
		vec2 g = uB.xy - (uA.xy + (e.xy / IMG - 0.5) * uA.zw);
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
	col *= uB.w;
	fragColor = TDOutputSwizzle(col);
}
