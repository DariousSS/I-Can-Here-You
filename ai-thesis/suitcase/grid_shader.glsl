// 纯白网格（被子的封面/待机画面，贴在 Kantan 的「格子初始」形状上）
// uG = (横向格数, 线宽（以一格为 1）, 亮度 0~1, 0)；画布 1920x1200，格子是正方形，四周有一圈边框线
uniform vec4 uG;
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	float cells = max(uG.x, 1.0);
	float asp = 1920.0 / 1200.0;
	vec2 g = vec2(uv.x * cells, uv.y * cells / asp);
	vec2 fr = fract(g);
	vec2 d = min(fr, 1.0 - fr);
	float w = max(uG.y, 0.002) * 0.5;
	float line = 1.0 - smoothstep(w * 0.6, w, min(d.x, d.y));
	float e = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
	float frame = 1.0 - smoothstep(0.0015, 0.0035, e);
	float v = max(line, frame) * uG.z;
	fragColor = TDOutputSwizzle(vec4(vec3(v), 1.0));
}
