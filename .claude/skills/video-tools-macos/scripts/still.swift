import AVFoundation
import AppKit
// args: src time out.jpg
let a=CommandLine.arguments; let g=AVAssetImageGenerator(asset:AVURLAsset(url:URL(fileURLWithPath:a[1])))
g.appliesPreferredTrackTransform=true; g.maximumSize=CGSize(width:1920,height:1920); g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
let cg=try! g.copyCGImage(at:CMTime(seconds:Double(a[2])!,preferredTimescale:600),actualTime:nil)
try! NSBitmapImageRep(cgImage:cg).representation(using:.jpeg,properties:[.compressionFactor:0.92])!.write(to:URL(fileURLWithPath:a[3]))
