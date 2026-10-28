// 面具上的脸"唱歌"：嘴那一块鼓起、纵向拉开，下巴跟着弯曲地往下掉，嘴心轻轻变暗（纯变形，没有画上去的东西）
// 输入 0 = 面具纹理（已裁成脸椭圆并放大铺满）
// uM = (张嘴程度 0~1, 嘴的位置 x, 嘴的位置 y（从上往下，0~1）, 0)
uniform vec4 uM;

out vec4 fragColor;

float sm(float x)
{
	x = clamp(x, 0.0, 1.0);
	return x * x * (3.0 - 2.0 * x);
}

void main()
{
	vec2 uv = vUV.st;
	float a = uM.x;
	if (a <= 0.002) {
		fragColor = TDOutputSwizzle(texture(sTD2DInputs[0], uv));
		return;
	}
	vec2 p = vec2(uv.x, 1.0 - uv.y);
	vec2 c = uM.yz;
	float r = length(vec2((p.x - c.x) / 0.26, (p.y - c.y) / 0.17));
	float f = 1.0 - sm(r);
	vec2 s = vec2(c.x + (p.x - c.x) / (1.0 + 0.55 * a * f), c.y + (p.y - c.y) / (1.0 + 2.6 * a * f));
	float jaw = sm((p.y - (c.y - 0.02)) / 0.14) * (1.0 - sm((p.y - 0.88) / 0.12)) * (1.0 - sm(abs(p.x - c.x) / 0.45));
	s.y -= 0.07 * a * jaw;
	s.x = c.x + (s.x - c.x) / (1.0 + 0.04 * a);
	vec2 q = clamp(vec2(s.x, 1.0 - s.y), 0.0, 1.0);
	vec4 col = texture(sTD2DInputs[0], q);
	float dx = (p.x - c.x) / 0.09;
	float dy = (p.y - (c.y + 0.02 * a)) / (0.015 + 0.05 * a);
	col.rgb *= 1.0 - 0.5 * a * exp(-(dx * dx) - (dy * dy));
	fragColor = TDOutputSwizzle(col);
}
