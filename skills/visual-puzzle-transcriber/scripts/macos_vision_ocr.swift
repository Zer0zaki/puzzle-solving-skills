import AppKit
import Foundation
import Vision

struct OCRCandidate: Codable {
    let text: String
    let confidence: Float
}

struct OCRItem: Codable {
    let engine: String
    let text: String
    let confidence: Float
    let bbox: [Double]
    let candidates: [OCRCandidate]
}

struct OCRPayload: Codable {
    let engine: String
    let width: Int
    let height: Int
    let items: [OCRItem]
}

guard CommandLine.arguments.count >= 2 else {
    fputs("usage: macos_vision_ocr.swift IMAGE [language1,language2] [fast|accurate]\n", stderr)
    exit(2)
}

let imagePath = CommandLine.arguments[1]
let languages = CommandLine.arguments.count >= 3
    ? CommandLine.arguments[2].split(separator: ",").map(String.init)
    : ["zh-Hans", "en-US"]
let level = CommandLine.arguments.count >= 4 ? CommandLine.arguments[3] : "accurate"

guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fputs("cannot load image: \(imagePath)\n", stderr)
    exit(3)
}

let request = VNRecognizeTextRequest()
request.recognitionLevel = level == "fast" ? .fast : .accurate
request.usesLanguageCorrection = true
request.recognitionLanguages = languages

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
do {
    try handler.perform([request])
} catch {
    fputs("Vision OCR failed: \(error)\n", stderr)
    exit(4)
}

let width = cgImage.width
let height = cgImage.height
let observations = (request.results ?? []).sorted {
    if abs($0.boundingBox.midY - $1.boundingBox.midY) > 0.02 {
        return $0.boundingBox.midY > $1.boundingBox.midY
    }
    return $0.boundingBox.minX < $1.boundingBox.minX
}

let items = observations.compactMap { observation -> OCRItem? in
    let top = observation.topCandidates(3)
    guard let best = top.first else { return nil }
    let box = observation.boundingBox
    let x = box.minX * Double(width)
    let y = (1.0 - box.maxY) * Double(height)
    let w = box.width * Double(width)
    let h = box.height * Double(height)
    return OCRItem(
        engine: "vision-\(level)",
        text: best.string,
        confidence: best.confidence,
        bbox: [x, y, w, h],
        candidates: top.map { OCRCandidate(text: $0.string, confidence: $0.confidence) }
    )
}

let payload = OCRPayload(engine: "vision-\(level)", width: width, height: height, items: items)
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys]
let data = try encoder.encode(payload)
FileHandle.standardOutput.write(data)
FileHandle.standardOutput.write("\n".data(using: .utf8)!)
