// 棋盘 8x8（TouchDesigner GLSL TOP 的像素着色器）：分成四个 4x4 的象限，每个象限一种排列方式，各自换脸；一格 YOU 留给观众（没有评判）
// 输入 0 = 脸的图集（4x4 格：0~11 爆开脸，12 此刻的实时脸，13 标准脸 CelebA/Lucy，14 标准脸 FairFace 平均，15 此刻实时脸的 AI 注意力叠图）
// uA  = (时间, 被"看着"的格子编号 -1~63, 测试目标格编号 -1~63, 总开关 0~1)
// uQ0~uQ3（左上、右上、左下、右下象限）= (白格用的脸, 黑格的处理：0 AI 注意力叠图(白格是实时脸时) / 1 反色 / 2 蜡笔马赛克 / 3 另一张脸, 黑格用的另一张脸（处理为 3 时）, 蜡笔马赛克覆盖程度 0~1)
// uY  = (YOU 格的编号 0~63, 0, 0, 0)
uniform vec4 uA;
uniform vec4 uQ0;
uniform vec4 uQ1;
uniform vec4 uQ2;
uniform vec4 uQ3;
uniform vec4 uY;

out vec4 fragColor;

vec4 quadInfo(int i)
{
	if (i == 0) { return uQ0; }
	if (i == 1) { return uQ1; }
	if (i == 2) { return uQ2; }
	return uQ3;
}

vec4 face(int k, vec2 q)
{
	float col = mod(float(k), 4.0);
	float row = floor(float(k) / 4.0);
	vec2 qq = clamp(q, 0.004, 0.996);
	return texture(sTD2DInputs[0], vec2((col + qq.x) / 4.0, (3.0 - row + qq.y) / 4.0));
}

vec4 faceM(int k, vec2 q, float amt)
{
	if (amt > 0.001) {
		float bl = mix(200.0, 9.0, amt);
		q = (floor(q * bl) + 0.5) / bl;
	}
	vec4 c = face(k, q);
	c.rgb = mix(c.rgb, floor(c.rgb * 7.0 + 0.5) / 7.0, amt);
	return c;
}

float hash(vec2 p)
{
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main()
{
	if (uA.w <= 0.001) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	vec2 uv = vUV.st;
	vec2 g = vec2(uv.x, 1.0 - uv.y) * 8.0;
	ivec2 cc = ivec2(clamp(floor(g), vec2(0.0), vec2(7.0)));
	int idx = cc.y * 8 + cc.x;
	vec2 cuv = vec2(fract(g.x), 1.0 - fract(g.y));
	int qd = (cc.y / 4) * 2 + (cc.x / 4);
	vec4 qi = quadInfo(qd);
	bool white = ((cc.x + cc.y) % 2) == 0;
	vec3 col = white ? vec3(0.93, 0.91, 0.96) : vec3(0.07, 0.055, 0.11);
	vec2 q = (cuv - 0.5) / 0.90 + 0.5;
	bool inFace = (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0);
	int wf = int(qi.x + 0.5);
	float amt = qi.w;
	if (idx == int(uY.x + 0.5)) {
		vec2 d = abs(cuv - 0.5);
		float m = max(d.x, d.y);
		float fr = (m > 0.40 && m < 0.45) ? 1.0 : 0.0;
		vec2 e = (cuv - 0.5) / vec2(0.19, 0.27);
		float ov = (abs(length(e) - 1.0) < 0.08) ? 1.0 : 0.0;
		float pulse = 0.5 + 0.5 * sin(uA.x * 2.0);
		col = mix(vec3(0.07, 0.055, 0.11), vec3(1.0), max(fr, ov * (0.45 + 0.55 * pulse)));
	} else if (inFace) {
		if (white) {
			col = faceM(wf, q, amt).rgb;
		} else {
			int mode = int(qi.y + 0.5);
			if (mode == 0) {
				col = (wf == 12) ? faceM(15, q, amt).rgb : (vec3(1.0) - faceM(wf, q, amt).rgb);
			} else if (mode == 1) {
				col = vec3(1.0) - faceM(wf, q, amt).rgb;
			} else if (mode == 2) {
				vec2 blocks = vec2(9.0);
				vec2 id = floor(q * blocks);
				vec2 jt = (vec2(hash(id), hash(id + 3.7)) - 0.5) * 0.6 / blocks;
				vec3 c = faceM(wf, (id + 0.5) / blocks + jt, amt).rgb;
				float lum = dot(c, vec3(0.299, 0.587, 0.114));
				c = mix(vec3(lum), c, 1.4);
				c = floor(c * 7.0 + 0.5) / 7.0;
				c *= 0.85 + 0.25 * hash(floor(q * 60.0));
				col = c;
			} else {
				col = faceM(int(qi.z + 0.5), q, amt).rgb;
			}
		}
	}
	float e2 = max(abs(cuv.x - 0.5), abs(cuv.y - 0.5));
	if (uA.y > -0.5 && idx == int(uA.y + 0.5) && e2 > 0.455) {
		col = vec3(0.2, 0.95, 0.9);
	}
	if (uA.z > -0.5 && idx == int(uA.z + 0.5) && e2 > 0.425 && e2 < 0.48) {
		col = mix(col, vec3(1.0, 0.2, 0.7), 0.5 + 0.5 * sin(uA.x * 6.0));
	}
	float gap = min(min(fract(g.x), 1.0 - fract(g.x)), min(fract(g.y), 1.0 - fract(g.y)));
	col *= 0.85 + 0.15 * smoothstep(0.0, 0.012, gap);
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
