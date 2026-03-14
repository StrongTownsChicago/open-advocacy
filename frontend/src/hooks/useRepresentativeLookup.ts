import { useState } from 'react';
import { Entity } from '../types';
import { entityService } from '../services/entities';
import { useUserRepresentatives } from '../contexts/UserRepresentativesContext';

interface UseRepresentativeLookupReturn {
  address: string;
  representatives: Entity[];
  districts: string[];
  searched: boolean;
  loading: boolean;
  error: string | null;
  showToast: boolean;
  toastMessage: string;
  showBackModal: boolean;
  handleAddressChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: (event: React.FormEvent) => Promise<void>;
  clearSearch: () => void;
  handleCloseToast: (_event?: React.SyntheticEvent | Event, reason?: string) => void;
  setShowBackModal: (value: boolean) => void;
}

export const useRepresentativeLookup = (): UseRepresentativeLookupReturn => {
  const { userRepresentatives, userAddress, updateUserRepresentatives, clearUserRepresentatives } =
    useUserRepresentatives();

  const [address, setAddress] = useState<string>(userAddress || '');
  const [representatives, setRepresentatives] = useState<Entity[]>(userRepresentatives || []);
  const [districts, setDistricts] = useState<string[]>([]);
  const [searched, setSearched] = useState<boolean>(userRepresentatives.length > 0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string>('');
  const [showBackModal, setShowBackModal] = useState(false);

  const handleAddressChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setAddress(event.target.value);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!address.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await entityService.findByAddress(address);

      const reps: Entity[] = response.data;

      const foundDistricts = [];

      for (let i = 0; i < reps.length; i++) {
        const districtName = reps[i].district_name;
        if (districtName) {
          foundDistricts.push(districtName);
        }
      }

      setRepresentatives(reps);
      setDistricts(foundDistricts);
      setSearched(true);

      // Automatically save as user's representatives
      updateUserRepresentatives(reps, address, foundDistricts);

      // Show success toast
      setToastMessage(`Found ${reps.length} representatives for your address`);
      setShowToast(true);
      setShowBackModal(true);
    } catch (err) {
      setError('Failed to find representatives. Please try again.');
      console.error('Error fetching representatives:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearched(false);
    setRepresentatives([]);
    setAddress('');
    clearUserRepresentatives();
  };

  const handleCloseToast = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setShowToast(false);
  };

  return {
    address,
    representatives,
    districts,
    searched,
    loading,
    error,
    showToast,
    toastMessage,
    showBackModal,
    handleAddressChange,
    handleSubmit,
    clearSearch,
    handleCloseToast,
    setShowBackModal,
  };
};
