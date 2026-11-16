import AVFoundation
import AppKit
// stdin lines: path \t time \t outjpg
var cache:[String:AVAssetImageGenerator]=[:]
while let line=readLine() { let f=line.components(separatedBy:"\t")
 let g=cache[f[0]] ?? { let g=AVAssetImageGenerator(asset:AVURLAsset(url:URL(fileURLWithPath:f[0]))); g.appliesPreferredTrackTransform=true; g.maximumSize=CGSize(width:320,height:320); g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero; cache[f[0]]=g; return g }()
 if let cg=try? g.copyCGImage(at:CMTime(seconds:Double(f[1])!,preferredTimescale:600),actualTime:nil){ try? NSBitmapImageRep(cgImage:cg).representation(using:.jpeg,properties:[:])!.write(to:URL(fileURLWithPath:f[2])) } }
