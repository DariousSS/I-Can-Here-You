// 整个竖屏的线框书：两页纸的轮廓 + 装订线 + 页边的几层纸，按键时一张纸翻过去（只有线，黑底；字在别的长方形里）。
// uF = (翻页进度 0~1（1 = 静止）, 方向 +1 = 从右往左翻 / -1 = 从左往右翻, 画布宽高比, 时间)
// uC = (封面模式 0/1, 单页模式 0/1（1 = 只有一页：整个竖屏是一张纸，翻页时一条弯曲的页边从左扫到右）, 0, 0)
// uP = (线的亮度（已乘整体出现程度）, 线粗（占画面高度的比例）, 书边留白（占画面宽度）, 翻起的那页翘起多高)
uniform vec4 uF;
uniform vec4 uP;
uniform vec4 uC;
out vec4 fragColor;

float seg(vec2 p, vec2 a, vec2 b)
{
	vec2 pa = p - a;
	vec2 ba = b - a;
	float h = clamp(dot(pa, ba) / max(dot(ba, ba), 1e-6), 0.0, 1.0);
	return length(pa - ba * h);
}

float rectLine(vec2 p, vec2 lo, vec2 hi)
{
	float d = seg(p, vec2(lo.x, lo.y), vec2(hi.x, lo.y));
	d = min(d, seg(p, vec2(hi.x, lo.y), vec2(hi.x, hi.y)));
	d = min(d, seg(p, vec2(hi.x, hi.y), vec2(lo.x, hi.y)));
	d = min(d, seg(p, vec2(lo.x, hi.y), vec2(lo.x, lo.y)));
	return d;
}

// 翻页时那条弯曲的页边：p = 翻页进度 0~1，dirx < 0 = 从左往右扫，bulge = 页边弯多少
float flipCurve(vec2 P, float p, float dirx, vec2 lo, vec2 hi, float bulge)
{
	float e = p * p * (3.0 - 2.0 * p);
	float fu = (dirx < 0.0) ? e : 1.0 - e;
	float xf = lo.x + (hi.x - lo.x) * fu;
	float yy = clamp((P.y - lo.y) / (hi.y - lo.y), 0.0, 1.0);
	float xc = xf + bulge * sin(3.14159265 * yy);
	float inside = step(lo.y - 0.03, P.y) * step(P.y, hi.y + 0.03);
	return abs(P.x - xc) * 0.9 + (1.0 - inside) * 1e3;
}

void main()
{
	vec2 uv = vUV.st;
	float asp = max(uF.z, 0.2);
	if (uC.x > 0.5) {
		// 合着的书的封面：外框 + 里面两层框 + 左边的书脊（竖线和几道横棱）+ 书名上下的装饰线
		vec2 Pc = vec2(uv.x * asp, uv.y);
		float thc = max(uP.y, 0.0005) * 1.4;
		float aac = thc * 0.6;
		float d0 = 0.035;
		vec2 lo = vec2(d0, d0);
		vec2 hi = vec2(asp - d0, 1.0 - d0);
		float l = smoothstep(thc + aac, thc - aac, rectLine(Pc, lo, hi));
		l = max(l, smoothstep(thc + aac, thc - aac, rectLine(Pc, lo + 0.022, hi - 0.022)) * 0.75);
		l = max(l, smoothstep(thc * 0.8 + aac, thc * 0.8 - aac, rectLine(Pc, lo + 0.042, hi - 0.042)) * 0.45);
		float sx = d0 + 0.075;
		l = max(l, smoothstep(thc + aac, thc - aac, seg(Pc, vec2(sx, d0), vec2(sx, 1.0 - d0))) * 0.9);
		float ys[6] = float[6](0.10, 0.135, 0.17, 0.83, 0.865, 0.90);
		for (int i = 0; i < 6; i++) {
			l = max(l, smoothstep(thc * 0.8 + aac, thc * 0.8 - aac, seg(Pc, vec2(d0, ys[i]), vec2(sx, ys[i]))) * 0.8);
		}
		float ox0 = sx + 0.05;
		float ox1 = asp - d0 - 0.05;
		l = max(l, smoothstep(thc * 0.8 + aac, thc * 0.8 - aac, seg(Pc, vec2(ox0, 0.66), vec2(ox1, 0.66))) * 0.8);
		l = max(l, smoothstep(thc * 0.8 + aac, thc * 0.8 - aac, seg(Pc, vec2(ox0, 0.34), vec2(ox1, 0.34))) * 0.8);
		l = max(l, texture(sTD2DInputs[0], uv).r);                       // 书名
		float br = 0.88 + 0.12 * sin(uF.w * 2.0);                         // 轻轻呼吸，提醒观众"打开我"
		fragColor = TDOutputSwizzle(vec4(vec3(1.0, 0.93, 0.78) * l * uP.x * br, clamp(l * uP.x, 0.0, 1.0)));
		return;
	}
	if (uC.y > 0.5) {
		// 单页：整个竖屏一张纸（外框 + 里面一层淡框），右边和下边有几层纸的厚度；翻页时一条弯曲的页边从左扫到右，后面拖着几道淡淡的影子
		vec2 Pp = vec2(uv.x * asp, uv.y);
		float t1 = max(uP.y, 0.0005) * 1.3;
		float a1 = t1 * 0.6;
		float d0 = 0.06;
		vec2 lo = vec2(d0, d0);
		vec2 hi = vec2(asp - d0, 1.0 - d0);
		float l = smoothstep(t1 + a1, t1 - a1, rectLine(Pp, lo, hi));
		l = max(l, smoothstep(t1 * 0.8 + a1, t1 * 0.8 - a1, rectLine(Pp, lo + 0.018, hi - 0.018)) * 0.35);
		for (int k = 1; k <= 6; k++) {
			float o = float(k) * 0.0055;
			float al = 0.55 - float(k) * 0.07;
			float dR = seg(Pp, vec2(hi.x + o, lo.y - o * 0.6), vec2(hi.x + o, hi.y + o * 0.6));
			float dB = seg(Pp, vec2(lo.x, lo.y - o * 0.6), vec2(hi.x + o, lo.y - o * 0.6));
			l = max(l, smoothstep(t1 + a1, t1 - a1, min(dR, dB)) * al);
		}
		float p1 = clamp(uF.x, 0.0, 1.0);
		if (p1 > 0.001 && p1 < 0.999) {
			float bl = uP.w * sin(3.14159265 * p1);
			float dd = flipCurve(Pp, p1, uF.y, lo, hi, bl);
			l = max(l, smoothstep(t1 * 1.4 + a1, t1 * 1.4 - a1, dd));
			for (int q = 1; q <= 3; q++) {
				float pq = p1 - 0.07 * float(q);
				if (pq > 0.0) {
					float dq = flipCurve(Pp, pq, uF.y, lo, hi, uP.w * sin(3.14159265 * pq) * 0.8);
					l = max(l, smoothstep(t1 + a1, t1 - a1, dq) * (0.5 - float(q) * 0.13));
				}
			}
		}
		fragColor = TDOutputSwizzle(vec4(vec3(1.0, 0.93, 0.78) * l * uP.x, clamp(l * uP.x, 0.0, 1.0)));
		return;
	}
	float dirv = (uF.y >= 0.0) ? 1.0 : -1.0;
	float xv = (dirv > 0.0) ? uv.x : 1.0 - uv.x;
	vec2 P = vec2(xv * asp, uv.y);                // 横向乘宽高比，距离才是圆的
	float th = max(uP.y, 0.0005);
	float aa = th * 0.6;
	float mx = uP.z;
	float my = mx * 0.6;                          // 上下留白小一点，书撑满整个高度（纸边线往上下还要多出 0.03）
	float x0 = mx * asp;
	float x1 = (1.0 - mx) * asp;
	float xm = 0.5 * asp;
	float y0 = my;
	float y1 = 1.0 - my;

	// 静止的书：左右两页的轮廓 + 装订线 + 外面几层纸（越往外越淡）
	float d = min(rectLine(P, vec2(x0, y0), vec2(xm, y1)), rectLine(P, vec2(xm, y0), vec2(x1, y1)));
	float line = smoothstep(th + aa, th - aa, d);
	// 书的厚度：左右两边各一叠竖着的纸边线（越往外越多一层，亮度只轻轻递减），上下各一道细线收住
	for (int k = 1; k <= 14; k++) {
		float o = float(k) * 0.0048;
		float grow = float(k) * 0.0022;
		float al = 0.55 - float(k) * 0.025;           // 纸边线比书的轮廓淡
		float dL = seg(P, vec2(x0 - o * asp, y0 - grow), vec2(x0 - o * asp, y1 + grow));
		float dR = seg(P, vec2(x1 + o * asp, y0 - grow), vec2(x1 + o * asp, y1 + grow));
		line = max(line, smoothstep(th + aa, th - aa, min(dL, dR)) * al);
	}
	float kk = 14.0;
	float dT = seg(P, vec2(x0 - kk * 0.0048 * asp, y1 + kk * 0.0022), vec2(x1 + kk * 0.0048 * asp, y1 + kk * 0.0022));
	float dB = seg(P, vec2(x0 - kk * 0.0048 * asp, y0 - kk * 0.0022), vec2(x1 + kk * 0.0048 * asp, y0 - kk * 0.0022));
	line = max(line, smoothstep(th + aa, th - aa, min(dT, dB)) * 0.3);
	float ds = seg(P, vec2(xm, y0), vec2(xm, y1));
	line = max(line, smoothstep(th * 1.3 + aa, th * 1.3 - aa, ds));

	// 翻起来的那一页
	float p = clamp(uF.x, 0.0, 1.0);
	if (p > 0.001 && p < 0.999) {
		float e = p * p * (3.0 - 2.0 * p);
		float ang = e * 3.14159265;
		float c = cos(ang);
		float lift = uP.w * sin(ang);
		float W = x1 - xm;
		float tipx = xm + W * c;
		float dl = 1e3;
		for (int j = 0; j < 16; j++) {
			float t0 = float(j) / 16.0;
			float t1 = float(j + 1) / 16.0;
			float bx0 = xm + (tipx - xm) * t0;
			float bx1 = xm + (tipx - xm) * t1;
			float cu0 = lift * (1.0 - pow(1.0 - t0, 2.0));
			float cu1 = lift * (1.0 - pow(1.0 - t1, 2.0));
			dl = min(dl, seg(P, vec2(bx0, y1 + cu0), vec2(bx1, y1 + cu1)));
			dl = min(dl, seg(P, vec2(bx0, y0 + cu0), vec2(bx1, y0 + cu1)));
		}
		dl = min(dl, seg(P, vec2(tipx, y0 + lift), vec2(tipx, y1 + lift)));
		// 翻起的纸上几条淡淡的行线，像纸上写着字
		for (int r = 1; r <= 6; r++) {
			float yy = y0 + (y1 - y0) * float(r) / 7.0 + lift;
			float dr = seg(P, vec2(xm + (tipx - xm) * 0.12, yy), vec2(xm + (tipx - xm) * 0.88, yy));
			line = max(line, smoothstep(th * 0.7 + aa, th * 0.7 - aa, dr) * 0.35);
		}
		line = max(line, smoothstep(th * 1.2 + aa, th * 1.2 - aa, dl));
	}
	vec3 col = vec3(1.0, 0.93, 0.78) * line * uP.x;
	fragColor = TDOutputSwizzle(vec4(col, clamp(line * uP.x, 0.0, 1.0)));      // 黑底部分透明，别的形状的字才不会被它盖住
}
