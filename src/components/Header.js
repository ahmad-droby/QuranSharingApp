/**
 * Header component with navigation
 */
export const Header = ({ activeTab, setActiveTab, savedDesignsCount }) => (
  <header className="header">
    <div className="header-content">
      <div className="logo">
        <div className="logo-icon">☪</div>
        <span className="logo-text">Ayah Canvas</span>
      </div>
      <nav className="nav-tabs">
        <button
          className={`nav-tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          ✨ Create
        </button>
        <button
          className={`nav-tab ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          💾 Saved ({savedDesignsCount})
        </button>
      </nav>
    </div>
  </header>
);
