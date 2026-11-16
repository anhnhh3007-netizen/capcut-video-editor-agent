import AVFoundation
import AppKit
let a=CommandLine.arguments; let url=URL(fileURLWithPath:a[1]); let out=a[2]; let step=Double(a[3])!; let size=Double(a[4])!
let asset=AVURLAsset(url:url); let dur=CMTimeGetSeconds(asset.duration)
if let tr=asset.tracks(withMediaType:.video).first { print("fps",tr.nominalFrameRate) }
let g=AVAssetImageGenerator(asset:asset); g.appliesPreferredTrackTransform=true
g.maximumSize=CGSize(width:size,height:size); g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
var t=0.0; var i=0
while t<dur { if let cg=try? g.copyCGImage(at:CMTime(seconds:t,preferredTimescale:600),actualTime:nil) {
  let d=NSBitmapImageRep(cgImage:cg).representation(using:.jpeg,properties:[.compressionFactor:0.7])!
  try! d.write(to:URL(fileURLWithPath:String(format:"%@/f_%05d.jpg",out,i))) }
  t+=step; i+=1 }
print("dur",dur,"frames",i)
