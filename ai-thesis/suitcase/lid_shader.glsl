// 盖子的画面：永远是简笔画卧室；入侵时卧室"出故障"：一块块区域变成粗像素马赛克（线条仍然看得见）、少量格子往下掉、横向撕裂、颜色错位、偶尔闪一行
// 马赛克用"取一格里最亮的点"而不是取平均：黑底白线的线条不会被抹掉，只会变成一格一格的粗线
// 输入 0 = 卧室（sc_bed_x，整张拉伸进盖子形状）；输入 1 暂时没用到
// uS.x = 入侵程度 0~1（越大故障越多），uS.y = 时间（秒）；uR 不用（保留，避免旧参数报警）
uniform vec4 uR;
uniform vec4 uS;
out vec4 fragColor;

float hash(vec2 p)
{
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main()
{
	vec2 uv = vUV.st;
	float g = clamp(uS.x, 0.0, 1.0);
	float t = uS.y;
	vec2 id = floor(uv * vec2(64.0, 36.0));
	float r = hash(id);
	float f = clamp((g * 0.35 - r) * 2.5, 0.0, 0.9);
	float oy = f * f * (0.03 + 0.10 * hash(id + 3.1));
	float tick = floor(t * 8.0);
	float band = floor(uv.y * 28.0);
	float tear = (hash(vec2(band, tick)) - 0.5) * 0.06 * g * step(0.72, hash(vec2(band, 7.0)));
	vec2 q = vec2(uv.x + tear, uv.y + oy);
	float sp = 0.010 * g;
	vec3 col;
	col.r = texture(sTD2DInputs[0], vec2(q.x + sp, q.y)).r;
	col.g = texture(sTD2DInputs[0], q).g;
	col.b = texture(sTD2DInputs[0], vec2(q.x - sp, q.y)).b;
	vec2 grid = vec2(40.0, 22.0);
	vec2 bid = floor(q * grid);
	float pick = hash(bid + vec2(floor(t * 4.0) * 1.7, 5.3));
	float region = 0.3 + 0.7 * hash(floor(q * vec2(8.0, 5.0)) + 9.1);
	if (pick < g * 0.6 * region) {
		vec3 mx = vec3(0.0);
		for (int i = 0; i < 8; i++) {
			for (int j = 0; j < 8; j++) {
				vec2 s = (bid + (vec2(float(i), float(j)) + 0.5) / 8.0) / grid;
				mx = max(mx, texture(sTD2DInputs[0], s).rgb);
			}
		}
		vec3 tn = (hash(bid + 1.3) < 0.5) ? vec3(0.55, 1.0, 0.95) : vec3(1.0, 0.6, 0.95);
		col = min(mx * 1.3, vec3(1.0)) * mix(vec3(1.0), tn, 0.45);
	}
	col += vec3(0.10) * g * step(0.985, hash(vec2(band, floor(t * 12.0))));
	col += vec3(uR.z * 0.0);
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
