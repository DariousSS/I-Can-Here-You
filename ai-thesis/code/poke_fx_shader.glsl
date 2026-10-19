// 戳一下城堡的水波 + 故障特效（TouchDesigner GLSL TOP 的像素着色器）
// uPoke.xy = 戳点（画布 uv，左下角是 0,0）；uPoke.z = 戳了多少秒；uPoke.w = 强度（0 = 不起作用）
uniform vec4 uPoke;

out vec4 fragColor;

const float ASP = 1.7778;

void main()
{
	vec2 uv = vUV.st;
	float amp = uPoke.w;
	float age = uPoke.z;
	if (amp <= 0.0 || age < 0.0) {
		fragColor = TDOutputSwizzle(texture(sTD2DInputs[0], uv));
		return;
	}
	vec2 d = uv - uPoke.xy;
	d.x *= ASP;
	float r = length(d);
	float front = age * 0.50;
	float env = exp(-age * 1.1) * smoothstep(0.0, 0.05, age) * amp;
	float band = exp(-pow((r - front) * 5.5, 2.0));
	float wave = sin((r - front) * 48.0) * band * env;
	vec2 dir = d / max(r, 0.0001);
	dir.x /= ASP;
	vec2 off = dir * wave * 0.034;
	float row = floor(uv.y * 60.0);
	float h = fract(sin(row * 12.9898 + floor(age * 20.0) * 78.233) * 43758.5453);
	off.x += step(0.78, h) * band * env * (h - 0.89) * 0.22;
	float ca = band * env * 0.020;
	vec4 c0 = texture(sTD2DInputs[0], uv + off);
	vec4 col;
	col.r = texture(sTD2DInputs[0], uv + off + dir * ca).r;
	col.g = c0.g;
	col.b = texture(sTD2DInputs[0], uv + off - dir * ca).b;
	col.a = c0.a;
	fragColor = TDOutputSwizzle(col);
}
