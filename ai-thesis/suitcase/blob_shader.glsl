// 隔音棉上的"云朵 / 史莱姆"：万花筒只出现在一个不规则的、会呼吸的形状里
// 输入 0 = 万花筒（castle_xf）
// uB = (声音大小 0~1, 时间（秒）, 形状的宽高比, 入侵程度 0~1)
// 平静时（入侵程度 uB.w 接近 0）云朵完全不显示，入侵开始后才从小长大
// uC = (圆心 x, 圆心 y, 大小倍数（0 或不填 = 1）, 半圆开关：大于 0.5 = 只显示圆心下面那一半，平边朝上)，在形状自己的 0~1 坐标里：0.5,0.5 = 正中间（整圆）；0,0.5 = 平边在左的半圆；1,0.5 = 平边在右；0.5,0 = 平边在下；0.5,1 = 平边在上
uniform vec4 uB;
uniform vec4 uC;
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	vec3 k = texture(sTD2DInputs[0], uv).rgb;
	vec2 p = (uv - uC.xy) * vec2(uB.z, 1.0);
	float r = length(p);
	float a = atan(p.y, p.x + 0.0001);
	float t = uB.y;
	float s = clamp(0.10 + 0.75 * uB.w + 0.35 * uB.x, 0.0, 1.0);     // 小的时候更小，随 uB.w（第几天）慢慢长大
	float sz = (uC.z > 0.01) ? uC.z : 1.0;
	float wob = 1.0 + 0.22 * sin(3.0 * a + t * 1.3) + 0.15 * sin(5.0 * a - t * 1.9) + 0.07 * sin(2.0 * a + t * 0.8 + uB.x * 4.0) + 0.10 * uB.x * sin(7.0 * a + t * 6.0);
	float R = (0.06 + 0.30 * s) * wob * sz;
	vec2 dd = vec2(cos(a), sin(a));
	float lx = (dd.x > 0.0) ? ((1.0 - uC.x) * uB.z) / max(dd.x, 0.001) : (uC.x * uB.z) / max(-dd.x, 0.001);
	float ly = (dd.y > 0.0) ? (1.0 - uC.y) / max(dd.y, 0.001) : uC.y / max(-dd.y, 0.001);
	float Lm = min(lx, ly) * 0.9;
	R = Lm * tanh(R / Lm);
	float ap = smoothstep(0.03, 0.35, uB.w);
	R *= ap;
	float m = smoothstep(R, R - 0.035, r) * ap;
	if (uC.w > 0.5) m *= smoothstep(0.0, -0.01, (uv.y - uC.y));
	if (uC.w > 1.5) { m = ap; R = 9.0; }                                  // 结尾：整个形状一下子被万花筒盛满（uC.w = 2）      // 半圆：圆心以上不显示，平边朝上
	float rim = smoothstep(R - 0.08, R, r) * m;
	vec3 col = k * (0.9 + 0.6 * rim);
	fragColor = TDOutputSwizzle(vec4(col * m, m));
}
