import AVFoundation
// usage: scan out.tsv file1 file2 ...   -> per ~0.2s: file t bright sharp motion
let a=CommandLine.arguments; var out=""
for p in a.dropFirst(2) {
 let asset=AVURLAsset(url:URL(fileURLWithPath:p))
 guard let tr=asset.tracks(withMediaType:.video).first, let r=try? AVAssetReader(asset:asset) else { continue }
 let o=AVAssetReaderTrackOutput(track:tr,outputSettings:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_420YpCbCr8BiPlanarFullRange])
 o.alwaysCopiesSampleData=false; r.add(o); r.startReading()
 var prev:[Float]=[]; var n=0; let fps=Double(tr.nominalFrameRate); let step=max(1,Int(fps/5))
 let name=(p as NSString).lastPathComponent
 while let sb=o.copyNextSampleBuffer() { defer{n+=1}; if n%step != 0 {continue}
  guard let pb=CMSampleBufferGetImageBuffer(sb) else {continue}
  CVPixelBufferLockBaseAddress(pb,.readOnly)
  let w=CVPixelBufferGetWidthOfPlane(pb,0), h=CVPixelBufferGetHeightOfPlane(pb,0), bpr=CVPixelBufferGetBytesPerRowOfPlane(pb,0)
  let base=CVPixelBufferGetBaseAddressOfPlane(pb,0)!.assumingMemoryBound(to:UInt8.self)
  let gw=96, gh=54; var g=[Float](repeating:0,count:gw*gh)
  for y in 0..<gh { for x in 0..<gw { g[y*gw+x]=Float(base[(y*h/gh)*bpr + x*w/gw]) } }
  // sharpness on center crop full-res rows
  var sh:Float=0; var cnt=0
  for y in stride(from:h/4,to:3*h/4,by:6) { let row=base+y*bpr; for x in stride(from:w/4,to:3*w/4-2,by:3) { sh+=abs(Float(row[x])-Float(row[x+1])); cnt+=1 } }
  CVPixelBufferUnlockBaseAddress(pb,.readOnly)
  let br=g.reduce(0,+)/Float(g.count)
  var mo:Float=0; if !prev.isEmpty { for i in 0..<g.count { mo+=abs(g[i]-prev[i]) }; mo/=Float(g.count) }
  prev=g
  let t=CMTimeGetSeconds(CMSampleBufferGetPresentationTimeStamp(sb))
  out+=String(format:"%@\t%.3f\t%.1f\t%.2f\t%.2f\n",name,t,br,sh/Float(max(cnt,1)),mo)
 }
}
try! out.write(toFile:a[1],atomically:true,encoding:.utf8)
