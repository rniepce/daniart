import SwiftUI

/// Card premium para exibir uma obra de arte.
/// Design: glassmorphism escuro, cantos arredondados,
/// tipografia serif, tags como chips, e ❤️ com animação spring.
struct ObraCard: View {
    let obra: Obra
    let onLike: () -> Void
    
    @State private var pulsar = false
    @State private var appeared = false
    @State private var imageLoaded = false
    
    // Cores premium
    private let goldLight = Color(red: 0.95, green: 0.80, blue: 0.50)
    private let goldDark = Color(red: 0.85, green: 0.65, blue: 0.35)
    private let cardBg = Color(red: 0.12, green: 0.11, blue: 0.16)
    
    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // ── IMAGEM ──
            imageSection
            
            // ── INFO + LIKE ──
            infoSection
        }
        .background(cardBg)
        .clipShape(RoundedRectangle(cornerRadius: 20, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 20, style: .continuous)
                .stroke(
                    LinearGradient(
                        colors: [
                            Color.white.opacity(0.08),
                            Color.white.opacity(0.02),
                            .clear
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    ),
                    lineWidth: 1
                )
        )
        .shadow(color: Color.black.opacity(0.4), radius: 20, x: 0, y: 10)
        .shadow(color: goldDark.opacity(obra.curtiu ? 0.15 : 0), radius: 30, x: 0, y: 5)
        // Animação de entrada
        .opacity(appeared ? 1 : 0)
        .offset(y: appeared ? 0 : 30)
        .onAppear {
            withAnimation(.easeOut(duration: 0.6).delay(0.1)) {
                appeared = true
            }
        }
    }
    
    // MARK: - Image Section
    
    private var imageSection: some View {
        AsyncImage(url: URL(string: obra.imagem_url)) { phase in
            switch phase {
            case .empty:
                // Loading skeleton
                Rectangle()
                    .fill(
                        LinearGradient(
                            colors: [
                                Color.white.opacity(0.03),
                                Color.white.opacity(0.06),
                                Color.white.opacity(0.03)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(height: 350)
                    .overlay(
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: goldLight.opacity(0.5)))
                            .scaleEffect(1.2)
                    )
                
            case .success(let image):
                image
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxWidth: .infinity, maxHeight: 500)
                    .background(Color.black.opacity(0.3))
                    .overlay(
                        // Degradê no fundo da imagem para legibilidade
                        LinearGradient(
                            colors: [
                                .clear,
                                .clear,
                                cardBg.opacity(0.3),
                                cardBg.opacity(0.8)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
                    .transition(.opacity.animation(.easeIn(duration: 0.4)))
                
            case .failure:
                Rectangle()
                    .fill(Color.white.opacity(0.04))
                    .frame(height: 350)
                    .overlay(
                        VStack(spacing: 8) {
                            Image(systemName: "photo.artframe")
                                .font(.system(size: 30))
                                .foregroundColor(.white.opacity(0.2))
                            Text("Imagem indisponível")
                                .font(.system(size: 12, design: .serif))
                                .foregroundColor(.white.opacity(0.2))
                        }
                    )
                
            @unknown default:
                EmptyView()
            }
        }
    }
    
    // MARK: - Info Section
    
    private var infoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top, spacing: 12) {
                // Título + Tags
                VStack(alignment: .leading, spacing: 8) {
                    Text(obra.titulo)
                        .font(.system(size: 20, weight: .medium, design: .serif))
                        .foregroundColor(.white.opacity(0.9))
                        .lineLimit(2)
                    
                    // Tags como chips
                    if !obra.tagsArray.isEmpty {
                        HStack(spacing: 6) {
                            ForEach(obra.tagsArray, id: \.self) { tag in
                                Text(tag.uppercased())
                                    .font(.system(size: 9, weight: .bold))
                                    .tracking(1.5)
                                    .foregroundColor(goldLight.opacity(0.7))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(
                                        Capsule()
                                            .fill(goldDark.opacity(0.1))
                                            .overlay(
                                                Capsule()
                                                    .stroke(goldDark.opacity(0.2), lineWidth: 0.5)
                                            )
                                    )
                            }
                        }
                    }
                }
                
                Spacer(minLength: 8)
                
                // Botão ❤️
                likeButton
            }
        }
        .padding(18)
    }
    
    // MARK: - Like Button
    
    private var likeButton: some View {
        Button(action: {
            // Haptic feedback
            let impact = UIImpactFeedbackGenerator(style: .medium)
            impact.impactOccurred()
            
            // Animação spring
            withAnimation(.spring(response: 0.3, dampingFraction: 0.5, blendDuration: 0)) {
                pulsar = true
            }
            
            onLike()
            
            // Reset do pulso
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) {
                    pulsar = false
                }
            }
        }) {
            ZStack {
                // Glow atrás do coração quando curtido
                if obra.curtiu {
                    Circle()
                        .fill(Color.red.opacity(0.15))
                        .frame(width: 50, height: 50)
                        .blur(radius: 8)
                }
                
                Image(systemName: obra.curtiu ? "heart.fill" : "heart")
                    .font(.system(size: 26, weight: .regular))
                    .foregroundStyle(
                        obra.curtiu
                        ? AnyShapeStyle(
                            LinearGradient(
                                colors: [
                                    Color(red: 1.0, green: 0.25, blue: 0.25),
                                    Color(red: 0.85, green: 0.15, blue: 0.30)
                                ],
                                startPoint: .top,
                                endPoint: .bottom
                            )
                        )
                        : AnyShapeStyle(Color.white.opacity(0.3))
                    )
                    .scaleEffect(pulsar ? 1.4 : (obra.curtiu ? 1.05 : 1.0))
            }
            .frame(width: 48, height: 48)
        }
        .buttonStyle(.plain)
    }
}


#Preview {
    ZStack {
        Color(red: 0.06, green: 0.06, blue: 0.10)
            .ignoresSafeArea()
        
        ObraCard(
            obra: Obra(
                id: 1,
                titulo: "Explosão Cósmica em Carmim",
                imagem_url: "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/1280px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
                tags_extraidas: "impasto, expressionismo, azul",
                curtiu: true
            ),
            onLike: {}
        )
        .padding(20)
    }
    .preferredColorScheme(.dark)
}
