import HeroBanner from "../components/landing/HeroBanner";
import LandingPanel from "../components/landing/LandingPanel";
import FeatureGrid from "../components/landing/FeatureGrid";
import DemoTeaser from "../components/landing/DemoTeaser";
import HowItWorks from "../components/landing/HowItWorks";
import CtaBanner from "../components/landing/CtaBanner";

export default function LandingPage() {
  return (
    <div className="space-y-8">
      <section className="grid items-start gap-10 pt-4 lg:grid-cols-[1.05fr_0.95fr]">
        <HeroBanner />
        <LandingPanel />
      </section>
      <FeatureGrid />
      <DemoTeaser />
      <HowItWorks />
      <CtaBanner />
    </div>
  );
}
