import Foundation

/// ViewModel que gerencia a comunicação com o servidor Python.
/// Carrega o feed diário e envia likes.
@MainActor
class FeedViewModel: ObservableObject {
    @Published var obras: [Obra] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String?
    
    // Para desenvolvimento local, use localhost.
    // Em produção, troque para a URL do Railway.
    private let baseUrl: String = {
        #if targetEnvironment(simulator)
        return "http://127.0.0.1:8000"
        #else
        return "http://127.0.0.1:8000" // Trocar pela URL do Railway
        #endif
    }()
    
    /// Carrega o feed de obras do dia
    func carregarFeed() async {
        isLoading = true
        errorMessage = nil
        
        guard let url = URL(string: "\(baseUrl)/feed/hoje") else {
            errorMessage = "URL inválida"
            isLoading = false
            return
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(from: url)
            
            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                errorMessage = "Servidor indisponível"
                isLoading = false
                return
            }
            
            let decoder = JSONDecoder()
            let feed = try decoder.decode([Obra].self, from: data)
            self.obras = feed
        } catch {
            errorMessage = "Erro ao carregar: \(error.localizedDescription)"
        }
        
        isLoading = false
    }
    
    /// Envia like/unlike para a API e atualiza localmente
    func darLike(obraId: Int) {
        // Encontra o índice da obra
        guard let index = obras.firstIndex(where: { $0.id == obraId }) else { return }
        
        // Atualiza a UI imediatamente (otimista)
        obras[index].curtiu.toggle()
        
        // Envia para o servidor em background
        guard let url = URL(string: "\(baseUrl)/obra/\(obraId)/like") else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        Task {
            do {
                let _ = try await URLSession.shared.data(for: request)
            } catch {
                // Se falhar, reverte o like
                await MainActor.run {
                    if let idx = self.obras.firstIndex(where: { $0.id == obraId }) {
                        self.obras[idx].curtiu.toggle()
                    }
                }
            }
        }
    }
}
