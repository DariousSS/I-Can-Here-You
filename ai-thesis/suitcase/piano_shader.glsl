// 字幕下面的小钢琴：36 个白键 + 25 个黑键（从 C 开始，和游戏里琴键编号一致）。平时淡淡的影子，按下的键亮起来（暖金色）。
// uS = 四个位掩码：按过的白键 0~17 / 18~35，按过的黑键 0~12 / 13~24（按过的键留一个暗金色，提醒这一句已经看过了）
// uV = (整体可见度 0~1（只有听故事的时候才出现）, 0, 0, 0)
// uP = (形状宽高比（装配脚本按 Kantan 里的形状自动写）, 按下的种类 0 没有 / 1 白键 / 2 黑键, 键序号（白 0~35，黑 0~24）, 亮度 0~1)
uniform vec4 uP;
uniform vec4 uS;
uniform vec4 uV;
out vec4 fragColor;

bool seenW(int i) {
	int m = (i < 18) ? int(uS.x + 0.5) : int(uS.y + 0.5);
	int k = (i < 18) ? i : i - 18;
	return ((m >> k) & 1) == 1;
}
bool seenB(int j) {
	int m = (j < 13) ? int(uS.z + 0.5) : int(uS.w + 0.5);
	int k = (j < 13) ? j : j - 13;
	return ((m >> k) & 1) == 1;
}

void main()
{
	vec2 uv = vUV.st;
	float asp = max(uP.x, 0.5);
	float wx = uv.x * 36.0;
	float wi = floor(wx);
	float fx = fract(wx);
	vec3 gold = vec3(1.0, 0.82, 0.45);
	float lit = uP.w;
	// 黑键：第 j 个黑键在白键 7*(j/5)+[0,1,3,4,5][j%5] 的右边缘；宽 0.62 个白键，高 0.6
	float bw = 0.62;
	float by = 0.40;
	float onBlack = 0.0;
	float bIdx = -1.0;
	for (int j = 0; j < 25; j++) {
		int oc = j / 5;
		int k = j - oc * 5;
		float off = (k == 0) ? 0.0 : (k == 1) ? 1.0 : (k == 2) ? 3.0 : (k == 3) ? 4.0 : 5.0;
		float cx = (float(oc) * 7.0 + off + 1.0);
		if (abs(wx - cx) < bw * 0.5 && uv.y > by) {
			onBlack = 1.0;
			bIdx = float(j);
		}
	}
	vec3 col = vec3(0.0);
	if (onBlack > 0.5) {
		col = vec3(0.04);
		if (seenB(int(bIdx))) {
			col = gold * 0.40;
		}
		if (uP.y > 1.5 && abs(bIdx - uP.z) < 0.5) {
			col = gold * lit;
		}
	} else {
		float edge = smoothstep(0.0, 0.08, fx) * smoothstep(0.0, 0.08, 1.0 - fx);
		col = vec3(0.20) * edge;
		if (seenW(int(wi))) {
			col = gold * 0.45 * edge;
		}
		if (uP.y > 0.5 && uP.y < 1.5 && abs(wi - uP.z) < 0.5) {
			col = gold * lit * edge;
		}
	}
	// 按下的键周围的柔光（让观众一眼看到是哪个）
	float cxp = 0.0;
	if (uP.y > 0.5 && lit > 0.01) {
		if (uP.y < 1.5) {
			cxp = (uP.z + 0.5) / 36.0;
		} else {
			float oc2 = floor(uP.z / 5.0);
			float k2 = uP.z - oc2 * 5.0;
			float off2 = (k2 < 0.5) ? 0.0 : (k2 < 1.5) ? 1.0 : (k2 < 2.5) ? 3.0 : (k2 < 3.5) ? 4.0 : 5.0;
			cxp = (oc2 * 7.0 + off2 + 1.0) / 36.0;
		}
		float d = length(vec2((uv.x - cxp) * asp, uv.y - 0.5));
		col += gold * 0.35 * lit * exp(-d * 9.0);
	}
	fragColor = TDOutputSwizzle(vec4(col * uV.x, 1.0));
}
