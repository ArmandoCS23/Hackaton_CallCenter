import bgImage from 'figma:asset/6ce4cf1b60b4ea35ca8572387034eb58c641f720.png';

export default function BackgroundPattern() {
  return (
    <>
      {/* Background Image */}
      <img
        src={bgImage}
        alt=""
        className="fixed inset-0 w-full h-full object-cover pointer-events-none"
      />
    </>
  );
}
