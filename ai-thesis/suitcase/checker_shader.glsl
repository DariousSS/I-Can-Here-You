// 红蓝格子（被子的封面/待机画面，也用作行李箱发亮时的纹理）
// uC = (横向格数, 亮度 0~1, 时间（秒）, 0)；画布 1920x1200，格子是正方形
uniform vec4 uC;
out vec4 fragColor;

void main()
{
	vec2 uv = vUV.st;
	float cells = max(uC.x, 1.0);
	float asp = 1920.0 / 1200.0;
	vec2 g = vec2(uv.x * cells, uv.y * cells / asp);
	vec2 id = floor(g);
	float odd = mod(id.x + id.y, 2.0);
	vec3 red = vec3(1.0, 0.12, 0.28);
	vec3 blue = vec3(0.12, 0.10, 1.0);
	vec3 col = mix(red, blue, odd);
	float shimmer = 0.84 + 0.16 * sin(uC.z * 1.3 + id.x * 0.6 + id.y * 0.9);
	fragColor = TDOutputSwizzle(vec4(col * shimmer * uC.y, 1.0));
}
