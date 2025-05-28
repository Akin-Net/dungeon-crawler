// frontend/src/components/sprites/OrcSprite.jsx
import React from 'react';

const OrcSprite = () => {
  return (
    <>
      <span className="orc-component orc-head">
        <span className="orc-component orc-eye orc-left-eye"></span>
        <span className="orc-component orc-eye orc-right-eye"></span>
      </span>
      <span className="orc-component orc-tusk orc-left-tusk"></span>
      <span className="orc-component orc-tusk orc-right-tusk"></span>
      <span className="orc-component orc-body"></span>
    </>
  );
};

export default OrcSprite;