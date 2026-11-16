import AVFoundation
let a=CommandLine.arguments; let asset=AVURLAsset(url:URL(fileURLWithPath:a[1]))
let st=Double(a[3])!, en=Double(a[4])!, fade=Double(a[5])!
let ex=AVAssetExportSession(asset:asset,presetName:AVAssetExportPresetAppleM4A)!
ex.outputURL=URL(fileURLWithPath:a[2]); ex.outputFileType = .m4a
ex.timeRange=CMTimeRange(start:CMTime(seconds:st,preferredTimescale:44100),end:CMTime(seconds:en,preferredTimescale:44100))
let p=AVMutableAudioMixInputParameters(track:asset.tracks(withMediaType:.audio)[0])
p.setVolumeRamp(fromStartVolume:1,toEndVolume:0,timeRange:CMTimeRange(start:CMTime(seconds:en-fade,preferredTimescale:44100),end:CMTime(seconds:en,preferredTimescale:44100)))
let mix=AVMutableAudioMix(); mix.inputParameters=[p]; ex.audioMix=mix
let sem=DispatchSemaphore(value:0); ex.exportAsynchronously{sem.signal()}; sem.wait(); print("export",ex.status.rawValue,ex.error ?? "")
