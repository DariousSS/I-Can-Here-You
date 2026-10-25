// 天使"转过来"：把整层画面当成一张竖着的卡片，绕竖轴转 theta 角，带透视（离屏幕边缘近的一侧更远、更小），再把城堡的范围切掉（天使不会盖到箱子上）。
// uT   = (转轴的画布位置 x, y（像素，y 向上）, theta（弧度，0 = 正对观众）, 透视强度 1/焦距)
// uB0~uB7 = 最多 8 个城堡方块各自的范围 (左, 下, 右, 上)（像素，y 向上，已留边距；没用到的是 0）
// uM   = (方向 +1 右边探头 / -1 左边探头, 是否切掉城堡范围 0/1, 身体歪的角度 phi（弧度，平面内旋转，像木头手斜着伸进来）, 0)
uniform vec4 uT;
uniform vec4 uB0;
uniform vec4 uB1;
uniform vec4 uB2;
uniform vec4 uB3;
uniform vec4 uB4;
uniform vec4 uB5;
uniform vec4 uB6;
uniform vec4 uB7;
uniform vec4 uM;

out vec4 fragColor;

const vec2 RES = vec2(1920.0, 1080.0);

bool inBox(vec2 f, vec4 b)
{
	return f.x > b.x && f.x < b.z && f.y > b.y && f.y < b.w;
}

void main()
{
	vec2 frag = vUV.st * RES;
	float th = uT.z;
	float s = sin(th);
	float c = cos(th);
	float k = uT.w;
	vec2 d = frag - uT.xy;
	float cp = cos(uM.z);
	float sp = sin(uM.z);
	d = vec2(cp * d.x + sp * d.y, -sp * d.x + cp * d.y);
	float X = d.x * uM.x;
	float den = c - X * s * k;
	vec4 col = vec4(0.0);
	if (den > 0.03) {
		float u = X / den;
		float v = d.y * (1.0 + u * s * k);
		vec2 src = uT.xy + vec2(u * uM.x, v);
		vec2 suv = src / RES;
		if (suv.x >= 0.0 && suv.x <= 1.0 && suv.y >= 0.0 && suv.y <= 1.0) {
			col = texture(sTD2DInputs[0], suv);
		}
	}
	if (uM.y > 0.5 && (inBox(frag, uB0) || inBox(frag, uB1) || inBox(frag, uB2) || inBox(frag, uB3) || inBox(frag, uB4) || inBox(frag, uB5) || inBox(frag, uB6) || inBox(frag, uB7))) {
		col = vec4(0.0);
	}
	fragColor = TDOutputSwizzle(col);
}
