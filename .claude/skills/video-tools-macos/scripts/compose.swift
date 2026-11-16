import AVFoundation
import Foundation
// compose PLAN.json OUT.mp4 — quick preview render (no CapCut needed).
// PLAN.json: {"width":1080,"height":1920,"fps":30,"audio":"/path/music.m4a"(optional),"audio_start":0.0,
//             "segments":[{"path":"/clip.MP4","src_in":2.0,"dur":0.5}, …]}
// Every clip is scaled to FILL the frame (centre crop), cut back-to-back; audio (if any) under the whole thing.
struct Seg: Decodable { let path: String; let src_in: Double; let dur: Double }
struct Plan: Decodable { let width: Int; let height: Int; let fps: Int?; let audio: String?; let audio_start: Double?; let segments: [Seg] }
let args = CommandLine.arguments
let plan = try! JSONDecoder().decode(Plan.self, from: Data(contentsOf: URL(fileURLWithPath: args[1])))
let final = URL(fileURLWithPath: args[2]); try? FileManager.default.removeItem(at: final)
let out = plan.audio == nil ? final : final.deletingLastPathComponent().appendingPathComponent("._video_only_" + final.lastPathComponent); try? FileManager.default.removeItem(at: out)
let comp = AVMutableComposition()
let vtrack = comp.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
let size = CGSize(width: plan.width, height: plan.height)
let fps = Int32(plan.fps ?? 30)
let layer = AVMutableVideoCompositionLayerInstruction(assetTrack: vtrack)   // one layer, transform changes at each cut
var cursor = CMTime.zero
for s in plan.segments {
  let asset = AVURLAsset(url: URL(fileURLWithPath: s.path))
  guard let src = asset.tracks(withMediaType: .video).first else { print("skip (no video):", s.path); continue }
  let dur = CMTime(seconds: s.dur, preferredTimescale: 600)
  let range = CMTimeRange(start: CMTime(seconds: s.src_in, preferredTimescale: 600), duration: dur)
  try! vtrack.insertTimeRange(range, of: src, at: cursor)
  let realEnd = vtrack.timeRange.end            // actual inserted length (frame-aligned)
  let nat = src.naturalSize.applying(src.preferredTransform); let w = abs(nat.width), h = abs(nat.height)
  let sc = max(size.width / w, size.height / h)
  var t = src.preferredTransform
  // move rotated content back to origin, then scale & centre
  let r = CGRect(origin: .zero, size: src.naturalSize).applying(src.preferredTransform)
  t = t.concatenating(CGAffineTransform(translationX: -r.minX, y: -r.minY))
  t = t.concatenating(CGAffineTransform(scaleX: sc, y: sc))
  t = t.concatenating(CGAffineTransform(translationX: (size.width - w * sc) / 2, y: (size.height - h * sc) / 2))
  layer.setTransform(t, at: cursor)
  cursor = realEnd
}
let whole = AVMutableVideoCompositionInstruction(); whole.timeRange = CMTimeRange(start: .zero, duration: max(comp.duration, cursor)); whole.layerInstructions = [layer]
let vc = AVMutableVideoComposition(); vc.renderSize = size; vc.frameDuration = CMTime(value: 1, timescale: fps); vc.instructions = [whole]
let ex = AVAssetExportSession(asset: comp, presetName: AVAssetExportPreset1920x1080)!
ex.outputURL = out; ex.outputFileType = .mp4; ex.videoComposition = vc
let sem = DispatchSemaphore(value: 0); ex.exportAsynchronously { sem.signal() }; sem.wait()
if ex.status == .completed, let ap = plan.audio {
  // pass 2: rendered pictures + music, passthrough (no re-render)
  let v = AVURLAsset(url: out), m = AVURLAsset(url: URL(fileURLWithPath: ap))
  let c2 = AVMutableComposition(); let vt = c2.addMutableTrack(withMediaType: .video, preferredTrackID: kCMPersistentTrackID_Invalid)!
  let vsrc = v.tracks(withMediaType: .video)[0]; try! vt.insertTimeRange(vsrc.timeRange, of: vsrc, at: .zero)
  if let asrc = m.tracks(withMediaType: .audio).first {
    let at = c2.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid)!
    let a0 = CMTime(seconds: plan.audio_start ?? 0, preferredTimescale: 44100)
    try? at.insertTimeRange(CMTimeRange(start: a0, duration: vsrc.timeRange.duration), of: asrc, at: .zero)
  }
  let ex2 = AVAssetExportSession(asset: c2, presetName: AVAssetExportPresetHighestQuality)!; ex2.outputURL = final; ex2.outputFileType = .mp4
  let s2 = DispatchSemaphore(value: 0); ex2.exportAsynchronously { s2.signal() }; s2.wait()
  try? FileManager.default.removeItem(at: out)
  print("audio mux", ex2.status == .completed ? "OK" : "FAILED \(String(describing: ex2.error))")
}
print("export", ex.status == .completed ? "OK" : "FAILED \(String(describing: ex.error))", String(format: "%.2fs", CMTimeGetSeconds(cursor)), final.path)
