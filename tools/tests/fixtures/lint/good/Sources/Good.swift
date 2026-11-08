func discount(for tier: Int) -> Int {
    guard tier > 0 else { return 0 }
    return tier * 5
}
