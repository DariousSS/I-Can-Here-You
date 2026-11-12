import AVFoundation

// 用法：mid2wav 输入.mid 输出.wav 总秒数 [音色编号，默认0=三角钢琴]
let args = CommandLine.arguments
if args.count < 4 { print("用法: mid2wav in.mid out.wav seconds [program]"); exit(2) }
let midiURL = URL(fileURLWithPath: args[1])
let outURL = URL(fileURLWithPath: args[2])
let total = Double(args[3]) ?? 10
let program = UInt8(args.count > 4 ? (Int(args[4]) ?? 0) : 0)

let engine = AVAudioEngine()
let sampler = AVAudioUnitSampler()
engine.attach(sampler)
engine.connect(sampler, to: engine.mainMixerNode, format: nil)
let format = AVAudioFormat(standardFormatWithSampleRate: 44100, channels: 2)!
do {
    try engine.enableManualRenderingMode(.offline, format: format, maximumFrameCount: 4096)
    let dls = URL(fileURLWithPath: "/System/Library/Components/CoreAudio.component/Contents/Resources/gs_instruments.dls")
    try sampler.loadSoundBankInstrument(at: dls, program: program,
                                        bankMSB: UInt8(kAUSampler_DefaultMelodicBankMSB),
                                        bankLSB: UInt8(kAUSampler_DefaultBankLSB))
    try engine.start()
    let seq = AVAudioSequencer(audioEngine: engine)
    try seq.load(from: midiURL, options: [])
    for t in seq.tracks { t.destinationAudioUnit = sampler }
    seq.prepareToPlay()
    try seq.start()
    let outFile = try AVAudioFile(forWriting: outURL, settings: [
        AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: 44100, AVNumberOfChannelsKey: 2,
        AVLinearPCMBitDepthKey: 16, AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false])
    let buf = AVAudioPCMBuffer(pcmFormat: engine.manualRenderingFormat, frameCapacity: engine.manualRenderingMaximumFrameCount)!
    let totalFrames = AVAudioFramePosition(total * 44100)
    var done: AVAudioFramePosition = 0
    while done < totalFrames {
        let n = AVAudioFrameCount(min(AVAudioFramePosition(buf.frameCapacity), totalFrames - done))
        let st = try engine.renderOffline(n, to: buf)
        if st == .success {
            try outFile.write(from: buf)
            done += AVAudioFramePosition(buf.frameLength)
        } else if st == .insufficientDataFromInputNode || st == .cannotDoInCurrentContext {
            continue
        } else { break }
    }
    print("OK \(done) frames")
} catch {
    print("出错: \(error)")
    exit(1)
}
