import { Composition } from "remotion";
import { Butterfly, TOTAL } from "./Butterfly";
import { FPS } from "./timeline";

export const RemotionRoot: React.FC = () => {
  return <Composition id="Butterfly" component={Butterfly} durationInFrames={TOTAL} fps={FPS} width={1920} height={1080} />;
};
