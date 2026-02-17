import SwiftUI

/// Tela principal — Feed de obras de arte curadas pela IA.
/// Design premium: dark mode, gradientes, tipografia serif.
struct ContentView: View {
    @StateObject private var viewModel = FeedViewModel()
    @State private var showSplash = true
    
    var body: some View {
        ZStack {
            // Background gradient escuro premium
            LinearGradient(
                colors: [
                    Color(red: 0.06, green: 0.06, blue: 0.10),
                    Color(red: 0.10, green: 0.08, blue: 0.14),
                    Color(red: 0.06, green: 0.06, blue: 0.10)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            if showSplash {
                // Splash animado
                splashView
            } else {
                // Conteúdo principal
                mainContent
            }
        }
        .onAppear {
            // Splash por 2 segundos, depois carrega o feed
            DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                withAnimation(.easeInOut(duration: 0.8)) {
                    showSplash = false
                }
                Task { await viewModel.carregarFeed() }
            }
        }
    }
    
    // MARK: - Splash Screen
    
    private var splashView: some View {
        VStack(spacing: 16) {
            Text("🎨")
                .font(.system(size: 80))
            
            Text("ArtAdvisor")
                .font(.system(size: 36, weight: .light, design: .serif))
                .foregroundStyle(
                    LinearGradient(
                        colors: [
                            Color(red: 0.85, green: 0.65, blue: 0.35),
                            Color(red: 0.95, green: 0.80, blue: 0.50),
                            Color(red: 0.85, green: 0.65, blue: 0.35)
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
            
            Text("Curadoria de Arte com IA")
                .font(.system(size: 14, weight: .regular, design: .serif))
                .foregroundColor(.white.opacity(0.5))
                .tracking(4)
                .textCase(.uppercase)
        }
        .transition(.opacity)
    }
    
    // MARK: - Main Content
    
    private var mainContent: some View {
        NavigationView {
            ScrollView(.vertical, showsIndicators: false) {
                VStack(spacing: 0) {
                    // Header
                    headerView
                    
                    // Content
                    if viewModel.isLoading {
                        loadingView
                    } else if let error = viewModel.errorMessage {
                        errorView(error)
                    } else if viewModel.obras.isEmpty {
                        emptyView
                    } else {
                        feedView
                    }
                }
                .padding(.bottom, 40)
            }
            .background(Color.clear)
            .navigationBarHidden(true)
            .refreshable {
                await viewModel.carregarFeed()
            }
        }
        .navigationViewStyle(.stack)
    }
    
    // MARK: - Header
    
    private var headerView: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Inspiração")
                        .font(.system(size: 34, weight: .bold, design: .serif))
                        .foregroundColor(.white)
                    
                    Text("do dia")
                        .font(.system(size: 34, weight: .light, design: .serif))
                        .foregroundStyle(
                            LinearGradient(
                                colors: [
                                    Color(red: 0.85, green: 0.65, blue: 0.35),
                                    Color(red: 0.95, green: 0.80, blue: 0.50)
                                ],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                }
                
                Spacer()
                
                // Ícone decorativo
                Image(systemName: "sparkles")
                    .font(.system(size: 22))
                    .foregroundStyle(
                        LinearGradient(
                            colors: [
                                Color(red: 0.85, green: 0.65, blue: 0.35),
                                Color(red: 0.95, green: 0.80, blue: 0.50)
                            ],
                            startPoint: .top,
                            endPoint: .bottom
                        )
                    )
            }
            
            // Linha separadora dourada
            Rectangle()
                .fill(
                    LinearGradient(
                        colors: [
                            Color(red: 0.85, green: 0.65, blue: 0.35).opacity(0.6),
                            Color(red: 0.95, green: 0.80, blue: 0.50).opacity(0.2),
                            .clear
                        ],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
                .frame(height: 1)
                .padding(.top, 8)
        }
        .padding(.horizontal, 20)
        .padding(.top, 60)
        .padding(.bottom, 24)
    }
    
    // MARK: - Loading State
    
    private var loadingView: some View {
        VStack(spacing: 20) {
            ForEach(0..<3, id: \.self) { _ in
                ShimmerCard()
            }
        }
        .padding(.horizontal, 20)
    }
    
    // MARK: - Error State
    
    private func errorView(_ message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 40))
                .foregroundColor(.white.opacity(0.3))
            
            Text(message)
                .font(.system(size: 15, design: .serif))
                .foregroundColor(.white.opacity(0.5))
                .multilineTextAlignment(.center)
            
            Button(action: {
                Task { await viewModel.carregarFeed() }
            }) {
                Text("Tentar novamente")
                    .font(.system(size: 14, weight: .medium))
                    .foregroundColor(Color(red: 0.95, green: 0.80, blue: 0.50))
                    .padding(.horizontal, 24)
                    .padding(.vertical, 12)
                    .background(
                        Capsule()
                            .stroke(Color(red: 0.85, green: 0.65, blue: 0.35).opacity(0.5), lineWidth: 1)
                    )
            }
        }
        .padding(.top, 80)
    }
    
    // MARK: - Empty State
    
    private var emptyView: some View {
        VStack(spacing: 20) {
            Image(systemName: "paintpalette")
                .font(.system(size: 50))
                .foregroundStyle(
                    LinearGradient(
                        colors: [
                            Color(red: 0.85, green: 0.65, blue: 0.35),
                            Color(red: 0.95, green: 0.80, blue: 0.50)
                        ],
                        startPoint: .top,
                        endPoint: .bottom
                    )
                )
            
            Text("O curador está preparando\nsua seleção de hoje")
                .font(.system(size: 17, design: .serif))
                .foregroundColor(.white.opacity(0.6))
                .multilineTextAlignment(.center)
                .lineSpacing(4)
            
            Text("Volte às 08:00 ✨")
                .font(.system(size: 13))
                .foregroundColor(.white.opacity(0.35))
        }
        .padding(.top, 80)
    }
    
    // MARK: - Feed
    
    private var feedView: some View {
        LazyVStack(spacing: 32) {
            ForEach(viewModel.obras) { obra in
                ObraCard(obra: obra) {
                    viewModel.darLike(obraId: obra.id)
                }
                .transition(.opacity.combined(with: .move(edge: .bottom)))
            }
        }
        .padding(.horizontal, 20)
        .animation(.easeInOut(duration: 0.4), value: viewModel.obras.count)
    }
}


// MARK: - Shimmer Loading Card

struct ShimmerCard: View {
    @State private var shimmerOffset: CGFloat = -200
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Image placeholder
            RoundedRectangle(cornerRadius: 16)
                .fill(Color.white.opacity(0.06))
                .frame(height: 380)
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .fill(
                            LinearGradient(
                                colors: [
                                    .clear,
                                    Color.white.opacity(0.05),
                                    .clear
                                ],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .offset(x: shimmerOffset)
                )
                .clipped()
            
            // Title placeholder
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.white.opacity(0.06))
                .frame(width: 180, height: 20)
            
            // Tags placeholder
            RoundedRectangle(cornerRadius: 6)
                .fill(Color.white.opacity(0.04))
                .frame(width: 120, height: 14)
        }
        .onAppear {
            withAnimation(.linear(duration: 1.5).repeatForever(autoreverses: false)) {
                shimmerOffset = 400
            }
        }
    }
}


#Preview {
    ContentView()
        .preferredColorScheme(.dark)
}
