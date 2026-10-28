// 城堡上的巨大拼脸（TouchDesigner GLSL TOP 的像素着色器）
// 整个城堡被当成一张大脸：顶上小方块 = 额头和头发，中间宽长方形 = 眼睛带（左眼、右眼），下面大方块 = 鼻子、嘴、下巴。
// 6 个零件各自来自不同的脸（用哪张由 uF0/uF1 给：额头A、左眼B、右眼C、鼻子D、嘴E、下巴F），脸来自输入 0 的图集（4x4 格：0~11 爆开脸，12 此刻的实时脸）；每块箱子各用一份这个着色器，只算自己那一块。
// uP = (这块箱子在"大脸"里的范围 左, 上, 右, 下)（0~1，y 向下）
// uQ = (接缝线强度 0~1, 像素化格数（0 = 照片）, 时间, 总开关 0~1)
uniform vec4 uP;
uniform vec4 uQ;
uniform vec4 uF0;
uniform vec4 uF1;

out vec4 fragColor;

vec4 pick(int part, vec2 f)
{
	float k = uF0.x;
	if (part == 1) { k = uF0.y; }
	if (part == 2) { k = uF0.z; }
	if (part == 3) { k = uF0.w; }
	if (part == 4) { k = uF1.x; }
	if (part == 5) { k = uF1.y; }
	float col = mod(k, 4.0);
	float row = floor(k / 4.0);
	vec2 ff = clamp(f, 0.004, 0.996);
	return texture(sTD2DInputs[0], vec2((col + ff.x) / 4.0, (3.0 - row + ff.y) / 4.0));
}

void main()
{
	if (uQ.w <= 0.001) {
		fragColor = TDOutputSwizzle(vec4(0.0));
		return;
	}
	vec2 uv = vUV.st;
	float fx = mix(uP.x, uP.z, uv.x);
	float fy = uP.y + (1.0 - uv.y) * (uP.w - uP.y);
	int part;
	if (fy < 0.22) {
		part = 0;
	} else if (fy < 0.525) {
		part = (fx < 0.5) ? 1 : 2;
	} else if (fy < 0.595) {
		part = 3;
	} else if (fy < 0.745) {
		part = 4;
	} else {
		part = 5;
	}
	vec2 f = vec2(0.1 + 0.8 * fx, 1.0 - fy);
	if (uQ.y > 0.5) {
		f = (floor(f * uQ.y) + 0.5) / uQ.y;
	}
	vec4 c = pick(part, f);
	float d = min(min(abs(fy - 0.22), abs(fy - 0.525)), min(abs(fy - 0.595), abs(fy - 0.745)));
	if (fy > 0.22 && fy < 0.525) {
		d = min(d, abs(fx - 0.5));
	}
	float seam = 1.0 - 0.55 * uQ.x * smoothstep(0.004, 0.0, d);
	fragColor = TDOutputSwizzle(vec4(c.rgb * seam, 1.0));
}
