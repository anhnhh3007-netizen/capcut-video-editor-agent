import AVFoundation
let a=CommandLine.arguments; let f=try! AVAudioFile(forReading:URL(fileURLWithPath:a[1]))
let sr=Double(a[3])!; let out=AVAudioFormat(commonFormat:.pcmFormatFloat32,sampleRate:sr,channels:1,interleaved:false)!
let conv=AVAudioConverter(from:f.processingFormat,to:out)!
let inBuf=AVAudioPCMBuffer(pcmFormat:f.processingFormat,frameCapacity:65536)!
var data=Data(); var done=false
while true { let ob=AVAudioPCMBuffer(pcmFormat:out,frameCapacity:65536)!
 var err:NSError?
 let st=conv.convert(to:ob,error:&err){n,s in if done {s.pointee = .endOfStream; return nil}
   do{ try f.read(into:inBuf) }catch{ done=true; s.pointee = .endOfStream; return nil }
   if inBuf.frameLength==0 {done=true; s.pointee = .endOfStream; return nil}
   s.pointee = .haveData; return inBuf }
 data.append(UnsafeBufferPointer(start:ob.floatChannelData![0],count:Int(ob.frameLength)))
 if st == .endOfStream || st == .error { break } }
try! data.write(to:URL(fileURLWithPath:a[2])); print(a[1].split(separator:"/").last!, Double(data.count/4)/sr,"s")
