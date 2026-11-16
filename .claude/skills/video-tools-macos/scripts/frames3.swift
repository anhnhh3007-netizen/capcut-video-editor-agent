import AVFoundation
import AppKit
let args = CommandLine.arguments
let out = args[1]
for path in args.dropFirst(2) {
  let url = URL(fileURLWithPath: path)
  let asset = AVURLAsset(url: url)
  let dur = CMTimeGetSeconds(asset.duration)
  let gen = AVAssetImageGenerator(asset: asset)
  gen.appliesPreferredTrackTransform = true
  gen.maximumSize = CGSize(width: 360, height: 360)
  gen.requestedTimeToleranceBefore = CMTime(seconds: 1, preferredTimescale: 600)
  gen.requestedTimeToleranceAfter = CMTime(seconds: 1, preferredTimescale: 600)
  let base = url.deletingPathExtension().lastPathComponent
  var i = 0
  for f in [0.15, 0.5, 0.85] {
    i += 1
    if let cg = try? gen.copyCGImage(at: CMTime(seconds: dur*f, preferredTimescale: 600), actualTime: nil) {
      let rep = NSBitmapImageRep(cgImage: cg)
      if let d = rep.representation(using: .jpeg, properties: [.compressionFactor: 0.6]) {
        try? d.write(to: URL(fileURLWithPath: "\(out)/\(base)_\(i).jpg"))
      }
    }
  }
  print("\(base)\t\(String(format: "%.1f", dur))")
}
