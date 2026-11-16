import AVFoundation
for p in CommandLine.arguments.dropFirst() { let a=AVURLAsset(url:URL(fileURLWithPath:p),options:[AVURLAssetPreferPreciseDurationAndTimingKey:true])
 let v=a.tracks(withMediaType:.video).first; let sz=v.map{$0.naturalSize.applying($0.preferredTransform)} ?? .zero
 print("\(p)\t\(Int64(CMTimeGetSeconds(a.duration)*1_000_000))\t\(Int(abs(sz.width)))\t\(Int(abs(sz.height)))\t\(a.tracks(withMediaType:.audio).count)") }
