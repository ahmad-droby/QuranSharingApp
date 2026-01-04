/**
 * Share modal component
 */
export const ShareModal = ({
  showShareModal,
  setShowShareModal,
  download,
  translationText,
  referenceText
}) => {
  if (!showShareModal) return null;

  return (
    <div className="modal-overlay" onClick={() => setShowShareModal(false)}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Share</h3>
          <button
            className="modal-close"
            onClick={() => setShowShareModal(false)}
          >
            ×
          </button>
        </div>
        <div className="social-btns">
          <button
            className="social-btn ig"
            onClick={() => {
              download();
              alert('Downloaded! Share on Instagram.');
              setShowShareModal(false);
            }}
          >
            📷 Instagram
          </button>
          <button
            className="social-btn fb"
            onClick={() => {
              window.open('https://www.facebook.com/sharer/sharer.php', '_blank');
              setShowShareModal(false);
            }}
          >
            👤 Facebook
          </button>
          <button
            className="social-btn tw"
            onClick={() => {
              window.open(
                `https://twitter.com/intent/tweet?text=${encodeURIComponent(`"${translationText.substring(0, 100)}..." - ${referenceText}`)}`,
                '_blank'
              );
              setShowShareModal(false);
            }}
          >
            🐦 Twitter
          </button>
          <button
            className="social-btn wa"
            onClick={() => {
              window.open(
                `https://wa.me/?text=${encodeURIComponent(`"${translationText.substring(0, 200)}..." - ${referenceText}`)}`,
                '_blank'
              );
              setShowShareModal(false);
            }}
          >
            💬 WhatsApp
          </button>
        </div>
      </div>
    </div>
  );
};
