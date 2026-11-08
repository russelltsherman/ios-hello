import SwiftUI

/// A greeting that updates as the user types their name.
public struct GreetingView: View {
    @State private var name = ""

    public init() {}

    public var body: some View {
        VStack(spacing: 16) {
            Text(Greeter.message(for: name))
                .font(.largeTitle)
            TextField("Your name", text: $name)
                .textFieldStyle(.roundedBorder)
                .frame(maxWidth: 240)
        }
        .padding(32)
    }
}
