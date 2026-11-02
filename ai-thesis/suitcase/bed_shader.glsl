// 第二台投影仪（天花板，投在床上）的画面：房间的放大地图 + 木头手（跟着手电筒的圈）+ 找到的光点（物品）亮起
// 输入 0 = 天使（sc_angel，默认关）；输入 1 = 当天的房间图（sc_room）；输入 2 = 木头手图（sc_woodhand）
// uS = (时间（秒）, 是否转 180 度 0/1（天花板投影仪倒挂时用）, 画布宽高比, 天使亮度 0~1)
// uA = (天使中心 x, y, 天使高度（占画布高度的比例）, 天使图的宽高比)
// uD = (光点 x, y（画布坐标 0~1，已缩进光点区 bed_dotbox）, 亮度 0~1（0 = 还没找到）, 出生时间（秒，和 uS.x 同一个钟）)
// uH = (木头手/圈 x, y（房间图坐标）, 手的透明度 0~1, 戳的程度 0~1)
// uR = (房间图宽高比, 房间图放大倍数, 房间的暗度（圈外亮度）, 圈的半径（房间图高度的比例）)
// uL = (方块左下角 x0, y0, 右上角 x1, y1，画布 0~1，转 180 度之后的画面坐标)
// uT = (镜像字小块的 x0, y0, x1, y1，画布 0~1；对位模式下有黄线框)
// uK = (对位模式 0/1（绿线框 + 红点=(x1,y1) 角 + 蓝点=(x0,y0) 角）, 万花筒亮度 0~1, 镜像字亮度 0~1, 0)；输入 1 = 万花筒人脸（原来是房间图，现在不用房间了）
// uP = (木头手大小（占画布高度）, 手悬浮上下晃的幅度, 是否画房间图 0/1（默认 0 = 背景黑）, 0)
uniform vec4 uS;
uniform vec4 uA;
uniform vec4 uD;
uniform vec4 uH;
uniform vec4 uR;
uniform vec4 uP;
uniform vec4 uL;
uniform vec4 uK;
uniform vec4 uT;
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	if (uS.y > 0.5) { uv = vec2(1.0) - uv; }
	float asp = max(uS.z, 0.1);
	float t = uS.x;
	float ra = max(uR.x, 0.1);
	vec2 rsize = vec2(max(uR.y, 0.05), max(uR.y, 0.05) * asp / ra);   // 房间图占画布的大小（宽按画布宽，保持比例）
	vec2 rq = (uv - 0.5) / rsize + 0.5;
	vec3 col = vec3(0.0);

	// 房间（暗），圈里亮；背景黑时只画圈的边
	if (rq.x > 0.0 && rq.x < 1.0 && rq.y > 0.0 && rq.y < 1.0) {
		float dh = length((rq - uH.xy) * vec2(ra, 1.0));
		float ring = uH.z * exp(-pow((dh - uR.w) / 0.012, 2.0)) * 0.30;
		col += vec3(1.0, 0.88, 0.6) * ring * step(0.001, uR.z);
		if (uP.z > 0.5) {
			vec3 room = texture(sTD2DInputs[1], rq).rgb;
			float torch = uH.z * smoothstep(uR.w, uR.w * 0.55, dh);
			col += room * (uR.z + (1.0 - uR.z) * torch);
			float dd = length((rq - uD.xy) * vec2(ra, 1.0));
			col += room * 1.6 * exp(-dd * 11.0) * uD.z;
		}
	}

	// 光点本身（画在房间上面）
	if (uD.z > 0.01) {
		vec2 dp = uD.xy;                                  // 已经由游戏缩进"光点区"（落在床上），直接是画布坐标
		float d = length((uv - dp) * vec2(asp, 1.0));
		float breath = 0.78 + 0.22 * sin(t * 1.6);
		float core = 1.5 * smoothstep(0.03, 0.0, d) + 0.75 * exp(-d * 13.0);
		float age = t - uD.w;
		if (age < -500.0) { age += 1000.0; }
		float flash = (age >= 0.0 && age < 6.0) ? exp(-age * 1.1) * 1.8 * exp(-d * 6.0) : 0.0;
		col += vec3(1.0, 0.9, 0.66) * (uD.z * core * breath + flash) + vec3(1.0, 0.8, 0.5) * 0.30 * exp(-d * 6.0) * uD.z;
	}

	// 天使（默认关）
	if (uS.w > 0.001) {
		vec2 p = uv - uA.xy;
		vec2 q = vec2(p.x * asp / (uA.z * uA.w) + 0.5, p.y / uA.z + 0.5);
		if (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0) {
			col += texture(sTD2DInputs[0], q).rgb * uS.w;
		}
	}

	// 木头手：指尖对准圈的中心；手图 1536x1024，指尖在 (0.791, 0.0967)
	if (uH.z > 0.01) {
		vec2 hc = 0.5 + (uH.xy - 0.5) * rsize;
		float hs = uP.x * (1.0 - 0.10 * uH.w);
		float bob = uP.y * sin(t * 2.0) * (1.0 - uH.w);
		vec2 tip = vec2(hc.x, hc.y + bob + 0.012 * (1.0 - uH.w));
		vec2 dq = vec2((uv.x - tip.x) * asp, uv.y - tip.y);
		vec2 q = vec2(0.791 + dq.x / (hs * 1.5), 0.0967 + dq.y / hs);
		// 手的影子（往左下偏一点）
		vec2 qs = q + vec2(0.012, 0.03) / hs * 0.6;
		if (qs.x > 0.0 && qs.x < 1.0 && qs.y > 0.0 && qs.y < 1.0) {
			col *= 1.0 - 0.45 * texture(sTD2DInputs[2], qs).a * uH.z;
		}
		if (q.x > 0.0 && q.x < 1.0 && q.y > 0.0 && q.y < 1.0) {
			vec4 h = texture(sTD2DInputs[2], q);
			col = mix(col, h.rgb, h.a * uH.z);
		}
	}
	// 左床方块（现在是矩形）：万花筒人脸（输入 1）完整放进 (x0,y0)-(x1,y1) 里，不会超出
	{
		vec2 lo = uL.xy, hi = max(uL.zw, uL.xy + 0.01);
		vec2 lq = (uv - lo) / (hi - lo);
		if (lq.x > 0.0 && lq.x < 1.0 && lq.y > 0.0 && lq.y < 1.0 && uK.y > 0.001) {
			vec2 e = min(lq, 1.0 - lq);
			float edge = smoothstep(0.0, 0.03, min(e.x, e.y));
			col = mix(col, texture(sTD2DInputs[1], lq).rgb, uK.y * edge);
		}
		if (uK.x > 0.5) {
			vec2 dd = max(lo - uv, uv - hi);
			float line = 1.0 - smoothstep(0.0, 0.004, abs(max(dd.x, dd.y)));
			col = mix(col, vec3(0.1, 1.0, 0.3), line);
			col = mix(col, vec3(1.0, 0.1, 0.1), 1.0 - smoothstep(0.012, 0.016, length((uv - hi) * vec2(asp, 1.0))));
			col = mix(col, vec3(0.2, 0.4, 1.0), 1.0 - smoothstep(0.012, 0.016, length((uv - lo) * vec2(asp, 1.0))));
		}
	}

	// 镜像字（输入 0 = sc_mirror_flip，左右反写的字，黑底）：单独一小块 (x0,y0)-(x1,y1)，暖白色
	if (uK.z > 0.001) {
		vec2 tlo = uT.xy, thi = max(uT.zw, uT.xy + 0.01);
		vec2 tq = (uv - tlo) / (thi - tlo);
		if (tq.x > 0.0 && tq.x < 1.0 && tq.y > 0.0 && tq.y < 1.0) {
			vec3 tx = texture(sTD2DInputs[0], tq).rgb;
			float ta = max(tx.r, max(tx.g, tx.b)) * uK.z;
			col = mix(col, vec3(1.0, 0.94, 0.78), clamp(ta, 0.0, 1.0));
		}
		if (uK.x > 0.5) {
			vec2 dt = max(tlo - uv, uv - thi);
			col = mix(col, vec3(1.0, 0.8, 0.1), 1.0 - smoothstep(0.0, 0.003, abs(max(dt.x, dt.y))));
		}
	}

	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
