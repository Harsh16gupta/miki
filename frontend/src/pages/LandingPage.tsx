import HeroBanner from "../components/landing/HeroBanner";
import FeatureGrid from "../components/landing/FeatureGrid";
import HowItWorks from "../components/landing/HowItWorks";
import CtaBanner from "../components/landing/CtaBanner";

export default function LandingPage() {
  return (
    <div className="space-y-4">
      <HeroBanner />
      <FeatureGrid />
      <HowItWorks />
      <CtaBanner />
    </div>
  );
}
