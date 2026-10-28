// 盖子的画面：永远是简笔画卧室；入侵时卧室"出故障"：像素块往下掉、横向撕裂、颜色错位、偶尔闪一行
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
	float f = clamp((g * 1.25 - r) * 2.5, 0.0, 1.0);
	float oy = f * f * (0.15 + 0.5 * hash(id + 3.1));
	float tick = floor(t * 8.0);
	float band = floor(uv.y * 28.0);
	float tear = (hash(vec2(band, tick)) - 0.5) * 0.08 * g * step(0.72, hash(vec2(band, 7.0)));
	vec2 q = vec2(uv.x + tear, uv.y + oy);
	float sp = 0.012 * g;
	vec3 col;
	col.r = texture(sTD2DInputs[0], vec2(q.x + sp, q.y)).r;
	col.g = texture(sTD2DInputs[0], q).g;
	col.b = texture(sTD2DInputs[0], vec2(q.x - sp, q.y)).b;
	col *= 1.0 - step(0.97, f);
	col += vec3(0.10) * g * step(0.985, hash(vec2(band, floor(t * 12.0))));
	col += vec3(uR.z * 0.0);
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
