import AVFoundation
let a=CommandLine.arguments; let asset=AVURLAsset(url:URL(fileURLWithPath:a[1]))
for m in asset.commonMetadata { print("meta",m.commonKey?.rawValue ?? "",m.value ?? "") }
let ex=AVAssetExportSession(asset:asset,presetName:AVAssetExportPresetAppleM4A)!
ex.outputURL=URL(fileURLWithPath:a[2]); ex.outputFileType = .m4a
let sem=DispatchSemaphore(value:0); ex.exportAsynchronously{sem.signal()}; sem.wait()
print("export",ex.status.rawValue, ex.error ?? "")
