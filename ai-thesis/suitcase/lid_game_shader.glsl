// 游戏用的盖子画面：房间是"乱的"（粗像素 + 横条错位 + 红蓝错位），只有手电筒照到的一圈是清楚的；光点只在被照到时才显出来
// 输入 0 = 当天的房间图（sc_room）
// uS = (乱的程度 0~1, 时间（秒）, 盖子形状的宽高比, 0)
// uF = (手电筒圆心 x, y（盖子自己的 0~1 坐标，y 向上）, 半径（以盖子高度为 1）, 手在不在 0/1)
// uD = (光点 x, y, 亮度 0~1, 0)
uniform vec4 uS;
uniform vec4 uF;
uniform vec4 uD;
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
	float asp = max(uS.z, 0.1);
	vec3 clearc = texture(sTD2DInputs[0], uv).rgb;
	vec2 cells = vec2(64.0, 34.0);
	vec2 cuv = (floor(uv * cells) + 0.5) / cells;
	vec3 pix = texture(sTD2DInputs[0], cuv).rgb * 0.26;
	float band = floor(uv.y * 26.0);
	float tick = floor(t * 8.0);
	float on = step(0.66, hash(vec2(band, tick)));
	float dx = (hash(vec2(band, tick + 9.0)) - 0.5) * 0.15 * on;
	vec3 sh;
	sh.r = texture(sTD2DInputs[0], vec2(uv.x + dx + 0.007, uv.y)).r;
	sh.g = texture(sTD2DInputs[0], vec2(uv.x + dx, uv.y)).g;
	sh.b = texture(sTD2DInputs[0], vec2(uv.x + dx - 0.007, uv.y)).b;
	float blk = step(0.75, hash(floor(uv * vec2(14.0, 8.0)) + vec2(floor(t * 3.0), 4.0)));
	vec3 gl = mix(pix, sh * 0.3, clamp(on * 0.75 + blk * 0.3, 0.0, 1.0));
	vec3 col = mix(clearc, gl, g);
	float R = max(uF.z, 0.001);
	float d = length((uv - uF.xy) * vec2(asp, 1.0));
	float vis = step(0.5, uF.w);
	float lit = (1.0 - smoothstep(R * 0.55, R, d)) * vis;
	col = mix(col, clearc * 0.75, lit);
	float ring = (1.0 - smoothstep(0.0, 0.012, abs(d - R))) * vis;
	col += vec3(1.0, 0.88, 0.58) * 0.7 * ring;
	float dd = length((uv - uD.xy) * vec2(asp, 1.0));
	col *= 1.0 - 0.6 * uD.z * exp(-dd * 22.0);
	col += vec3(1.0, 0.95, 0.7) * uD.z * (1.6 * smoothstep(0.045, 0.0, dd) + 0.7 * exp(-dd * 18.0));
	fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
