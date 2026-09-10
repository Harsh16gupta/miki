import HeroBanner from "../components/landing/HeroBanner";
import FeatureGrid from "../components/landing/FeatureGrid";

export default function LandingPage() {
  return (
    <div className="space-y-4">
      <HeroBanner />
      <FeatureGrid />
    </div>
  );
}
