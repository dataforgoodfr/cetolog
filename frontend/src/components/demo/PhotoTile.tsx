import Image from "next/image";
import { formatScore, sideLabel, type Side } from "@/demo/contract";

type PhotoTileProps = {
  imageId?: string;
  individu: string;
  side: Side;
  caption?: string;
  score?: number;
};

export function PhotoTile({
  imageId,
  individu,
  side,
  caption,
  score,
}: PhotoTileProps) {
  const label = sideLabel(side);

  return (
    <figure className="photo-tile">
      {imageId ? (
        <Image
          className="photo"
          src={`/api/demo/photos/${imageId}`}
          alt={`Photo ${label} de ${individu}`}
          width={400}
          height={260}
          unoptimized
        />
      ) : (
        <div
          className="photo photo-missing"
          role="img"
          aria-label={`Pas de photo ${label} pour ${individu}`}
        >
          pas de photo {label}
        </div>
      )}
      <figcaption className="photo-caption">
        {caption ??
          (imageId
            ? `${label} ${formatScore(score)}`
            : `pas de photo ${label}`)}
      </figcaption>
    </figure>
  );
}
