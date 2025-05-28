// frontend/src/components/sprites/OrcSprite.jsx
import React from 'react';

const SkeletonSprite = () => {
  return (
    <>
              <span className="skeleton-component skeleton-torso"></span>
              <span className="skeleton-component skeleton-bow">
                <span className="skeleton-component bow-string"></span>
              </span>
              <span className="skeleton-component skeleton-skull">
                {/* Eye sockets are pseudo-elements of skull */}
                <span className="skeleton-component skeleton-teeth-container">
                  <span className="skeleton-component skeleton-tooth"></span>
                  <span className="skeleton-component skeleton-tooth"></span>
                  <span className="skeleton-component skeleton-tooth"></span>
                  {/* Add more teeth if space allows */}
                </span>
              </span>
            </>
  );
};

export default SkeletonSprite;