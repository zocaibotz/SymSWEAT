import React, { useState, useEffect } from 'react';

const styleTokens = {
  colors: {
    primary: '#10B981',
    primary_variant: '#059669',
    secondary: '#3B82F6',
    background: '#F9FAFB',
    surface: '#FFFFFF',
    text_primary: '#111827',
    text_secondary: '#6B7280',
    warning_sugar: '#EF4444',
    success: '#34D399'
  },
  typography: {
    font_family: 'Inter, sans-serif',
    heading_1: '24px',
    heading_2: '20px',
    body: '16px',
    caption: '14px'
  },
  spacing: {
    base: '4px',
    card_padding: '16px',
    screen_margin: '24px',
    grid_gap: '12px'
  },
  effects: {
    card_shadow: '0 1px 3px rgba(0,0,0,0.1)',
    border_radius: '12px'
  }
};

const styles = {
  app: {
    fontFamily: styleTokens.typography.font_family,
    backgroundColor: styleTokens.colors.background,
    minHeight: '100vh',
    color: styleTokens.colors.text_primary
  },
  container: {
    maxWidth: '480px',
    margin: '0 auto',
    padding: styleTokens.spacing.screen_margin,
    paddingBottom: '80px'
  },
  header: {
    fontSize: styleTokens.typography.heading_1,
    fontWeight: '700',
    marginBottom: '24px',
    color: styleTokens.colors.text_primary
  },
  card: {
    backgroundColor: styleTokens.colors.surface,
    borderRadius: styleTokens.effects.border_radius,
    boxShadow: styleTokens.effects.card_shadow,
    padding: styleTokens.spacing.card_padding,
    marginBottom: styleTokens.spacing.grid_gap
  },
  summaryCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  metricBox: {
    textAlign: 'center',
    flex: 1
  },
  metricValue: {
    fontSize: '28px',
    fontWeight: '700',
    color: styleTokens.colors.primary
  },
  metricLabel: {
    fontSize: styleTokens.typography.caption,
    color: styleTokens.colors.text_secondary,
    marginTop: '4px'
  },
  metricValueSugar: {
    fontSize: '28px',
    fontWeight: '700',
    color: styleTokens.colors.warning_sugar
  },
  sectionTitle: {
    fontSize: styleTokens.typography.heading_2,
    fontWeight: '600',
    marginBottom: '12px',
    marginTop: '24px'
  },
  historyItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 0',
    borderBottom: '1px solid #E5E7EB'
  },
  historyImage: {
    width: '50px',
    height: '50px',
    borderRadius: '8px',
    backgroundColor: '#E5E7EB',
    objectFit: 'cover',
    marginRight: '12px'
  },
  historyDetails: {
    flex: 1
  },
  historyTitle: {
    fontWeight: '500',
    fontSize: styleTokens.typography.body
  },
  historyMeta: {
    fontSize: styleTokens.typography.caption,
    color: styleTokens.colors.text_secondary
  },
  historyCalories: {
    fontWeight: '600',
    color: styleTokens.colors.primary
  },
  fab: {
    position: 'fixed',
    bottom: '24px',
    right: '24px',
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: styleTokens.colors.primary,
    border: 'none',
    boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '24px'
  },
  captureContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '300px',
    backgroundColor: '#E5E7EB',
    borderRadius: styleTokens.effects.border_radius,
    marginBottom: '24px'
  },
  uploadIcon: {
    fontSize: '48px',
    color: styleTokens.colors.text_secondary,
    marginBottom: '16px'
  },
  captureText: {
    color: styleTokens.colors.text_secondary,
    marginBottom: '24px'
  },
  buttonRow: {
    display: 'flex',
    gap: '12px'
  },
  button: {
    padding: '12px 24px',
    borderRadius: styleTokens.effects.border_radius,
    fontSize: styleTokens.typography.body,
    fontWeight: '500',
    cursor: 'pointer',
    border: 'none',
    flex: 1
  },
  buttonPrimary: {
    backgroundColor: styleTokens.colors.primary,
    color: 'white'
  },
  buttonSecondary: {
    backgroundColor: styleTokens.colors.surface,
    color: styleTokens.colors.text_primary,
    border: '1px solid #E5E7EB'
  },
  processingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh'
  },
  spinner: {
    width: '48px',
    height: '48px',
    border: '4px solid #E5E7EB',
    borderTopColor: styleTokens.colors.primary,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  },
  processingText: {
    marginTop: '16px',
    color: styleTokens.colors.text_secondary
  },
  summaryImage: {
    width: '100%',
    height: '200px',
    objectFit: 'cover',
    borderRadius: styleTokens.effects.border_radius,
    marginBottom: '16px'
  },
  nutritionRow: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px 0',
    borderBottom: '1px solid #E5E7EB'
  },
  nutritionLabel: {
    color: styleTokens.colors.text_secondary
  },
  nutritionValue: {
    fontWeight: '600'
  },
  backButton: {
    position: 'fixed',
    top: '24px',
    left: '24px',
    backgroundColor: 'rgba(255,255,255,0.9)',
    border: 'none',
    borderRadius: '50%',
    width: '40px',
    height: '40px',
    cursor: 'pointer',
    fontSize: '18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: styleTokens.effects.card_shadow
  },
  emptyState: {
    textAlign: 'center',
    padding: '40px 20px',
    color: styleTokens.colors.text_secondary
  }
};

// Mock data for demonstration
const mockHistory = [
  { id: 1, name: 'Grilled Chicken Salad', calories: 380, sugar: 4, time: '2 hours ago', image: null },
  { id: 2, name: 'Apple & Almonds', calories: 195, sugar: 19, time: '5 hours ago', image: null },
  { id: 3, name: 'Oatmeal with Berries', calories: 280, sugar: 12, time: 'Yesterday', image: null }
];

const mockAnalysis = {
  food: 'Grilled Salmon with Vegetables',
  calories: 520,
  sugar: 8,
  protein: 42,
  carbs: 24,
  fat: 28
};

function App() {
  const [screen, setScreen] = useState('dashboard');
  const [history, setHistory] = useState(mockHistory);
  const [selectedImage, setSelectedImage] = useState(null);
  const [dailyStats, setDailyStats] = useState({ calories: 1250, sugar: 45 });

  const totalCalories = dailyStats.calories + history.reduce((sum, item) => sum + item.calories, 0);
  const totalSugar = dailyStats.sugar + history.reduce((sum, item) => sum + item.sugar, 0);

  const handleAddFood = () => {
    setScreen('capture');
  };

  const handleImageCapture = (e) => {
    const file = e.target.files[0];
    if (file) {
      const imageUrl = URL.createObjectURL(file);
      setSelectedImage(imageUrl);
      setScreen('processing');
      
      // Simulate AI processing
      setTimeout(() => {
        setScreen('summary');
      }, 2000);
    }
  };

  const handleConfirm = () => {
    const newEntry = {
      id: Date.now(),
      name: mockAnalysis.food,
      calories: mockAnalysis.calories,
      sugar: mockAnalysis.sugar,
      time: 'Just now',
      image: selectedImage
    };
    setHistory([newEntry, ...history]);
    setSelectedImage(null);
    setScreen('dashboard');
  };

  const handleDiscard = () => {
    setSelectedImage(null);
    setScreen('dashboard');
  };

  const renderDashboard = () => (
    <div style={styles.container}>
      <h1 style={styles.header}>Nutrition Tracker</h1>
      
      <div style={styles.card}>
        <div style={styles.summaryCard}>
          <div style={styles.metricBox}>
            <div style={styles.metricValue}>{totalCalories}</div>
            <div style={styles.metricLabel}>Calories</div>
          </div>
          <div style={styles.metricBox}>
            <div style={styles.metricValueSugar}>{totalSugar}g</div>
            <div style={styles.metricLabel}>Sugar</div>
          </div>
        </div>
      </div>

      <h2 style={styles.sectionTitle}>Recent Entries</h2>
      
      {history.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No food entries yet.</p>
          <p>Tap + to add your first meal!</p>
        </div>
      ) : (
        <div style={styles.card}>
          {history.map((item) => (
            <div key={item.id} style={styles.historyItem}>
              <div style={{...styles.historyImage, backgroundColor: item.image ? 'transparent' : '#E5E7EB'}}>
                {item.image && <img src={item.image} alt={item.name} style={styles.historyImage} />}
              </div>
              <div style={styles.historyDetails}>
                <div style={styles.historyTitle}>{item.name}</div>
                <div style={styles.historyMeta}>{item.time} • {item.sugar}g sugar</div>
              </div>
              <div style={styles.historyCalories}>{item.calories} cal</div>
            </div>
          ))}
        </div>
      )}

      <button style={styles.fab} onClick={handleAddFood}>
        +
      </button>
    </div>
  );

  const renderCapture = () => (
    <div style={styles.container}>
      <button style={styles.backButton} onClick={() => setScreen('dashboard')}>←</button>
      <h1 style={styles.header}>Add Food</h1>
      
      <div style={styles.captureContainer}>
        <div style={styles.uploadIcon}>📷</div>
        <p style={styles.captureText}>Take a photo or select from gallery</p>
        
        <div style={styles.buttonRow}>
          <label style={{...styles.button, ...styles.buttonPrimary, textAlign: 'center'}}>
            Take Photo
            <input 
              type="file" 
              accept="image/*" 
              capture="environment"
              onChange={handleImageCapture}
              style={{ display: 'none' }}
            />
          </label>
          <label style={{...styles.button, ...styles.buttonSecondary, textAlign: 'center', cursor: 'pointer'}}>
            Gallery
            <input 
              type="file" 
              accept="image/*"
              onChange={handleImageCapture}
              style={{ display: 'none' }}
            />
          </label>
        </div>
      </div>
    </div>
  );

  const renderProcessing = () => (
    <div style={styles.container}>
      <div style={styles.processingContainer}>
        <style>{`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
        <div style={styles.spinner}></div>
        <p style={styles.processingText}>Analyzing your meal...</p>
        <p style={{...styles.processingText, fontSize: '14px'}}>Identifying food items and calculating nutrition</p>
      </div>
    </div>
  );

  const renderSummary = () => (
    <div style={styles.container}>
      <button style={styles.backButton} onClick={handleDiscard}>←</button>
      <h1 style={styles.header}>Meal Summary</h1>
      
      {selectedImage && (
        <img src={selectedImage} alt="Food" style={styles.summaryImage} />
      )}
      
      <div style={styles.card}>
        <h2 style={{marginBottom: '16px', fontWeight: '600'}}>{mockAnalysis.food}</h2>
        
        <div style={styles.nutritionRow}>
          <span style={styles.nutritionLabel}>Calories</span>
          <span style={{...styles.nutritionValue, color: styleTokens.colors.primary}}>{mockAnalysis.calories} kcal</span>
        </div>
        <div style={styles.nutritionRow}>
          <span style={styles.nutritionLabel}>Sugar</span>
          <span style={{...styles.nutritionValue, color: styleTokens.colors.warning_sugar}}>{mockAnalysis.sugar}g</span>
        </div>
        <div style={styles.nutritionRow}>
          <span style={styles.nutritionLabel}>Protein</span>
          <span style={styles.nutritionValue}>{mockAnalysis.protein}g</span>
        </div>
        <div style={styles.nutritionRow}>
          <span style={styles.nutritionLabel}>Carbs</span>
          <span style={styles.nutritionValue}>{mockAnalysis.carbs}g</span>
        </div>
        <div style={{...styles.nutritionRow, borderBottom: 'none'}}>
          <span style={styles.nutritionLabel}>Fat</span>
          <span style={styles.nutritionValue}>{mockAnalysis.fat}g</span>
        </div>
      </div>

      <div style={styles.buttonRow}>
        <button style={{...styles.button, ...styles.buttonSecondary}} onClick={handleDiscard}>
          Discard
        </button>
        <button style={{...styles.button, ...styles.buttonPrimary}} onClick={handleConfirm}>
          Save Entry
        </button>
      </div>
    </div>
  );

  return (
    <div style={styles.app}>
      {screen === 'dashboard' && renderDashboard()}
      {screen === 'capture' && renderCapture()}
      {screen === 'processing' && renderProcessing()}
      {screen === 'summary' && renderSummary()}
    </div>
  );
}

export default App;
