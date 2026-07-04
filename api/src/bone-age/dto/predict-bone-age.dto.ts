import { IsEnum } from 'class-validator';

export enum Sex {
  male = 'male',
  female = 'female',
}

/**
 * Validated form fields for the bone-age prediction request.
 * The image itself is handled separately via the file interceptor.
 */
export class PredictBoneAgeDto {
  @IsEnum(Sex, { message: "sex must be either 'male' or 'female'" })
  sex!: Sex;
}
