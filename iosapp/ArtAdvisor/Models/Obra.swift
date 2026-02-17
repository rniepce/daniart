import Foundation

/// Modelo de uma obra de arte curada pela IA.
/// Corresponde exatamente ao JSON retornado pela API FastAPI.
struct Obra: Identifiable, Codable {
    let id: Int
    let titulo: String
    let imagem_url: String
    let tags_extraidas: String
    var curtiu: Bool
    
    /// Tags como array limpo para exibição
    var tagsArray: [String] {
        tags_extraidas
            .split(separator: ",")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }
}
