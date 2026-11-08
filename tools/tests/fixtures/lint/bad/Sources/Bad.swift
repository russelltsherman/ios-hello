func messy(_ a: Int, _ b: Int?) -> Int {
    var r = 0
    if a > 1 { r += 1 }
    if a > 2 { r += 1 }
    if a > 3 { r += 1 }
    if a > 4 { r += 1 }
    if a > 5 { r += 1 }
    if a > 6 { r += 1 }
    if a > 7 { r += 1 }
    if a > 8 { r += 1 }
    if a > 9 { r += 1 }
    if a > 10 { r += 1 }
    if a > 11 { r += 1 }
    if a > 12 { r += 1 }
    return r + b!
}
