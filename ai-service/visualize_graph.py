import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, Ellipse
from matplotlib import patheffects
import numpy as np
from typing import Dict, List, Tuple
import os

class LangSmithStyleVisualizer:
    def __init__(self):
        # LangSmith karanlık tema ayarları
        plt.rcParams['font.family'] = ['Inter', 'Segoe UI', 'Arial', 'sans-serif']
        plt.rcParams['font.size'] = 10
        
        self.fig, self.ax = plt.subplots(1, 1, figsize=(14, 16))
        # LangSmith karanlık arka plan
        self.background_color = '#111827'  # Sofistike koyu gri-lacivert
        self.fig.patch.set_facecolor(self.background_color)
        
        self.node_positions = {}
        
        # LangSmith canlı neon-pastel renk paleti
        self.node_colors = {
            'start_end': '#10B981',      # Canlı yeşil
            'process': '#38BDF8',        # Parlak camgöbeği
            'decision': '#F59E0B',       # Enerjik amber
            'tools': '#8B5CF6',          # Canlı mor
            'cache': '#2DD4BF',          # Turkuaz
            'error': '#EF4444'           # Parlak kırmızı
        }
        
        # Glow efekti için açık tonlar
        self.glow_colors = {
            'start_end': '#34D399',
            'process': '#60A5FA',
            'decision': '#FBBF24',
            'tools': '#A78BFA',
            'cache': '#5EEAD4',
            'error': '#F87171'
        }
        
        # Modern ikonlar
        self.node_icons = {
            'start': '▶️',
            'end': '🏁',
            'process': '⚙️',
            'decision': '🔀',
            'tools': '🔧',
            'cache': '💾',
            'validate': '✅',
            'ai': '🤖'
        }
    
    def add_glow_effect(self, x: float, y: float, width: float, height: float, 
                       color: str, shape: str = 'rect'):
        """LangSmith stil glow efekti"""
        glow_alpha = 0.15
        
        for i in range(3):
            glow_size = 1 + (i * 0.3)
            alpha = glow_alpha - (i * 0.05)
            
            if shape == 'diamond':
                glow = patches.RegularPolygon(
                    (x, y), 4, radius=(height/2 + 0.3) * glow_size,
                    orientation=np.pi/4,
                    facecolor=color, alpha=alpha, edgecolor='none'
                )
            elif shape == 'ellipse':
                glow = Ellipse((x, y), width * glow_size, height * glow_size,
                              facecolor=color, alpha=alpha, edgecolor='none')
            else:  # rectangle
                glow = FancyBboxPatch(
                    (x - (width * glow_size)/2, y - (height * glow_size)/2), 
                    width * glow_size, height * glow_size,
                    boxstyle="round,pad=0.15",
                    facecolor=color, alpha=alpha, edgecolor='none'
                )
            
            self.ax.add_patch(glow)
    
    def add_node(self, node_id: str, label: str, node_type: str, icon: str,
                 position: Tuple[float, float], size: Tuple[float, float] = (3.0, 1.3)):
        """LangSmith stil node'lar - ikon olmadan"""
        self.node_positions[node_id] = position
        x, y = position
        width, height = size
        
        main_color = self.node_colors[node_type]
        glow_color = self.glow_colors[node_type]
        
        # Glow efekti ekle
        if node_type == 'decision':
            self.add_glow_effect(x, y, width, height, glow_color, 'diamond')
        elif node_id in ['start', 'end']:
            self.add_glow_effect(x, y, width, height, glow_color, 'ellipse')
        else:
            self.add_glow_effect(x, y, width, height, glow_color, 'rect')
        
        # Ana şekil
        if node_type == 'decision':
            # Diamond şekli
            diamond = patches.RegularPolygon(
                (x, y), 4, radius=height/2 + 0.3,
                orientation=np.pi/4,
                facecolor=main_color,
                edgecolor='white',
                linewidth=2,
                alpha=0.9
            )
            self.ax.add_patch(diamond)
        elif node_id in ['start', 'end']:
            # Oval şekil
            oval = Ellipse((x, y), width, height,
                          facecolor=main_color,
                          edgecolor='white',
                          linewidth=2,
                          alpha=0.9)
            self.ax.add_patch(oval)
        else:
            # Rounded rectangle
            rect = FancyBboxPatch(
                (x - width/2, y - height/2), width, height,
                boxstyle="round,pad=0.12",
                facecolor=main_color,
                edgecolor='white',
                linewidth=2,
                alpha=0.9
            )
            self.ax.add_patch(rect)
        
        # Sadece label - ortalanmış, ikon yok
        self.ax.text(x, y, label, ha='center', va='center',
                    fontsize=10, fontweight='600', color='white',
                    linespacing=1.1)
    
    def add_edge_with_line_breaking_label(self, from_node: str, to_node: str, label: str = "",
                                        edge_type: str = "normal", curve_intensity: float = 0.2):
        """Çizgiyi kıran stil etiketli oklar"""
        if from_node not in self.node_positions or to_node not in self.node_positions:
            return
        
        x1, y1 = self.node_positions[from_node]
        x2, y2 = self.node_positions[to_node]
        
        # Edge renkleri
        if edge_type == "conditional":
            color = '#F59E0B'  # Amber
            linestyle = '--'
            linewidth = 2.5
        elif edge_type == "error":
            color = '#EF4444'  # Kırmızı
            linestyle = ':'
            linewidth = 2.5
        elif edge_type == "loop":
            color = '#8B5CF6'  # Mor
            linestyle = '-.'
            linewidth = 2.5
        else:
            color = '#10B981'  # Yeşil
            linestyle = '-'
            linewidth = 2.5
        
        # Curve calculation
        dx = x2 - x1
        dy = y2 - y1
        
        # Özel routing
        if edge_type == "loop":
            connectionstyle = f'arc3,rad=-0.4'
        elif from_node == "check_cache" and to_node == "cache_answer":
            connectionstyle = f'arc3,rad=-0.8'  # Büyük kavis sol dışarıdan
        elif from_node == "validate_input" and to_node == "end":
            connectionstyle = f'arc3,rad=0.45'
        elif abs(dx) > abs(dy):
            rad = 0.15 if dy >= 0 else -0.15
            connectionstyle = f'arc3,rad={rad}'
        else:
            connectionstyle = f'arc3,rad={curve_intensity}'
        
        # Ok çizimi
        self.ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(
                            arrowstyle='->',
                            connectionstyle=connectionstyle,
                            color=color,
                            linestyle=linestyle,
                            linewidth=linewidth,
                            shrinkA=24, shrinkB=24,
                            alpha=0.85
                        ))
        
        # Çizgiyi kıran etiket
        if label:
            # Etiket pozisyonu hesapla
            if 'arc3' in connectionstyle:
                rad_value = float(connectionstyle.split('rad=')[1])
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                
                # Kavis offset
                perp_x = -(y2 - y1)
                perp_y = (x2 - x1)
                length = np.sqrt(perp_x**2 + perp_y**2)
                if length > 0:
                    perp_x /= length
                    perp_y /= length
                
                curve_offset = rad_value * np.sqrt(dx**2 + dy**2) * 0.18
                label_x = mid_x + perp_x * curve_offset
                label_y = mid_y + perp_y * curve_offset
                
                # Özel pozisyonlama: Validation Error etiketini sola taşı
                if from_node == "validate_input" and to_node == "end" and label == "Validation Error":
                    label_x = label_x - 2.8  # Sola taşı
                    label_y = label_y + 2.8  # Biraz yukarı
                
                # Özel pozisyonlama: Back to Agent etiketini sola al ve yukarı taşı
                if from_node == "summarize_outputs" and to_node == "call_model" and label == "Back to Agent":
                    label_x = label_x - 1.0  # Sola al
                    label_y = label_y + 0.8  # Yukarı taşı
                
                # Özel pozisyonlama: Cache Hit etiketini sağa taşı
                if from_node == "check_cache" and to_node == "cache_answer" and label == "Cache Hit":
                    label_x = label_x + 4.2  # Sağa taşı
                    label_y = label_y + 1.2  # Hafif yukarı
                
                # Özel pozisyonlama: Direct Answer etiketini yukarı al
                if from_node == "should_continue" and to_node == "cache_answer" and label == "Direct Answer":
                    label_y = label_y + 0.9  # Yukarı al
                    label_x = label_x + 0.7  # Sağa taşı

            else:
                label_x, label_y = (x1 + x2) / 2, (y1 + y2) / 2
            
            # Çizgiyi kıran etiket - arka plan rengi şemanın arka planıyla aynı
            self.ax.text(label_x, label_y, label,
                        ha='center', va='center', fontsize=8,
                        fontweight='600', color=color,
                        bbox=dict(boxstyle="round,pad=0.3",
                                facecolor=self.background_color,  # Arka plan rengi
                                edgecolor='none',
                                alpha=1.0))  # Tam opak
    
    def create_langsmith_workflow(self):
        """LangSmith stil karanlık tema workflow - ikon olmadan"""
        
        # ANA OMURGA - kompakt spacing
        self.add_node('start', 'START', 'start_end', '', (0, 12))
        self.add_node('check_cache', 'Check\nCache', 'decision', '', (0, 9.5))
        self.add_node('validate_input', 'Validate\nInput', 'process', '', (0, 7))
        self.add_node('call_model', 'Call\nModel', 'process', '', (0, 4.5))
        self.add_node('should_continue', 'Should\nContinue?', 'decision', '', (0, 2))
        self.add_node('end', 'END', 'start_end', '', (0, -1))
        
        # YAN YOLLAR - simetrik
        self.add_node('execute_tools', 'Execute\nTools', 'tools', '', (-4.5, 0))
        self.add_node('summarize_outputs', 'Summarize\nOutputs', 'tools', '', (-4.5, -2))
        self.add_node('cache_answer', 'Cache\nAnswer', 'cache', '', (4.5, 0))
        
        # BAĞLANTILAR - çizgiyi kıran etiketlerle
        self.add_edge_with_line_breaking_label('start', 'check_cache', 'Begin')
        self.add_edge_with_line_breaking_label('check_cache', 'validate_input', 'Cache Miss', 'conditional', 0.03)
        self.add_edge_with_line_breaking_label('validate_input', 'call_model', 'Valid Input')
        self.add_edge_with_line_breaking_label('call_model', 'should_continue', 'Evaluate')
        
        self.add_edge_with_line_breaking_label('should_continue', 'execute_tools', 'Use Tools', 'conditional')
        self.add_edge_with_line_breaking_label('execute_tools', 'summarize_outputs', 'Process Results')
        self.add_edge_with_line_breaking_label('summarize_outputs', 'call_model', 'Back to Agent', 'loop')
        
        self.add_edge_with_line_breaking_label('should_continue', 'cache_answer', 'Direct Answer', 'conditional')
        self.add_edge_with_line_breaking_label('cache_answer', 'end', 'Complete')
        
        self.add_edge_with_line_breaking_label('check_cache', 'cache_answer', 'Cache Hit', 'conditional')
        self.add_edge_with_line_breaking_label('validate_input', 'end', 'Validation Error', 'error')
    
    def save_visualization(self, filename: str = "langsmith_style_workflow.png",
                          title: str = "LangGraph AI Assistant Workflow"):
        """LangSmith stil karanlık tema görselleştirme"""
        
        # Grafik ayarları
        self.ax.set_xlim(-7, 7)
        self.ax.set_ylim(-4, 14)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_facecolor(self.background_color)
        
        # LangSmith stil başlık
        title_text = self.ax.text(0, 13.5, title, ha='center', va='center',
                                 fontsize=18, fontweight='700', color='white')
        
        # Alt başlık - gri ton
        self.ax.text(0, 13, "Modern AI Assistant Architecture",
                    ha='center', va='center', fontsize=10,
                    style='italic', color='#9CA3AF')
        
        # Ana omurga vurgusu - çok ince
        backbone_line = plt.Line2D([0, 0], [11.8, -0.8], 
                                  color='#374151', linewidth=3, alpha=0.3, zorder=0)
        self.ax.add_line(backbone_line)
        
        # LangSmith stil legend - minimal (title_fontcolor kaldırıldı)
        legend_elements = [
            patches.Patch(color='#10B981', label='Start/End'),
            patches.Patch(color='#38BDF8', label='Processing'),
            patches.Patch(color='#F59E0B', label='Decision'),
            patches.Patch(color='#8B5CF6', label='Tools'),
            patches.Patch(color='#2DD4BF', label='Cache')
        ]
        
        legend = self.ax.legend(handles=legend_elements, 
                               loc='upper right', bbox_to_anchor=(0.98, 0.98),
                               frameon=True, fancybox=True,
                               fontsize=8, title="Components",
                               title_fontsize=9, 
                               facecolor='#1F2937', edgecolor='#374151',
                               labelcolor='white')
        
        # Legend başlığını manuel olarak beyaz yap
        legend.get_title().set_color('white')
        
        # Alt bilgi - LangSmith stil entegre
        workflow_info = """Main Backbone: START → Cache Check → Validation → AI Model → Decision → END
Side Paths: Tool Loop (left) • Cache Path (right) • Error Handling"""
        
        self.ax.text(0, -3, workflow_info, ha='center', va='center',
                    fontsize=8, color='#6B7280', style='italic',
                    linespacing=1.4)
        
        # Key Features - küçük font, az dikkat çekici
        key_features = """Cache-first strategy • Input validation & security • AI reasoning with tools • Intelligent summarization • Optimized response flow"""
        
        self.ax.text(0, -3.7, key_features, ha='center', va='center',
                    fontsize=7, color='#4B5563')
        
        # Kaydet - yüksek kalite
        plt.tight_layout()
        output_path = os.path.join(os.path.dirname(__file__), filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight',
                   facecolor=self.background_color, edgecolor='none',
                   pad_inches=0.3)
        
        print(f"🎨 LangSmith-style workflow saved: {output_path}")
        print(f"🌙 Dark mode theme applied")
        print(f"✨ Line-breaking labels integrated")
        print(f"🎯 SaaS monitoring interface aesthetic achieved")
        plt.show()
        return output_path

def main():
    """Ana fonksiyon"""
    print("🌙 LangSmith-Style Dark Mode Workflow Visualizer")
    print("=" * 55)
    print("🎨 Creating modern SaaS monitoring interface aesthetic")
    print("✨ Applying line-breaking label technique")
    print("🎯 Professional dark theme with neon-pastel colors")
    print()
    
    try:
        visualizer = LangSmithStyleVisualizer()
        visualizer.create_langsmith_workflow()
        path = visualizer.save_visualization()
        print(f"🎉 Successfully created LangSmith-style workflow: {path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()